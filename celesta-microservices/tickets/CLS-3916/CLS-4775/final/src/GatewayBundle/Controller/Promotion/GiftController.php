<?php

namespace App\GatewayBundle\Controller\Promotion;

use App\AppBundle\Helper\FormHelper;
use App\GatewayBundle\Form\Type\Promotion\Gift\OfferType;
use App\GatewayBundle\Form\Type\Promotion\Gift\QueryType;
use App\GatewayBundle\Manager\PermissionManager;
use App\GatewayBundle\Manager\PlayerManager;
use App\GatewayBundle\Manager\UserActivityJobManager;
use App\GatewayBundle\Normalizer\Promotion\GiftNormalizer;
use App\GatewayBundle\Normalizer\Promotion\GiftRequestNormalizer;
use App\Library\MemberZoneClient;
use App\Library\PromotionClient;
use App\OAuth2Bundle\Security\Authentication\OAuth2Authenticator;
use App\OAuth2Bundle\Security\User\User;
use CurlLibrary\Exception\V2Exception;
use GuzzleHttp\Exception\BadResponseException;
use OpenApi\Attributes as OA;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\Form\FormError;
use Symfony\Component\Form\FormInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Contracts\Translation\TranslatorInterface;

#[OA\Tag(name: 'Gift', description: 'Gift')]
class GiftController extends AbstractController
{
    use GiftRequestErrorTrait;

    private const string PS_GIFT_OFFER = 'PS_GIFT_OFFER';
    private const string PS_GIFT_REQUEST = 'PS_GIFT_REQUEST';

    public function __construct(
        private readonly PromotionClient $promotionClient,
        private readonly GiftNormalizer $giftNormalizer,
        private readonly FormHelper $formHelper,
        private readonly MemberZoneClient $memberZoneClient,
        private readonly PlayerManager $playerManager,
        private readonly TranslatorInterface $translator,
        private readonly UserActivityJobManager $userActivityJobManager,
        private readonly GiftRequestNormalizer $giftRequestNormalizer,
    ) {
    }

    #[OA\Post(
        path: '/api/gateway/domain/{domainId}/player/{playerId}/gift',
        summary: 'Offer gift',
        tags: ['Gift'],
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\PathParameter(name: 'playerId', required: true, schema: new OA\Schema(type: 'integer'), example: 1)]
    #[OA\RequestBody(required: true, content: new OA\JsonContent(ref: '#/components/schemas/GiftOfferRequest'))]
    #[OA\Response(
        response: '200',
        description: 'Recorded gift, or the gift request when the user may only request gifts',
        content: new OA\JsonContent(oneOf: [
            new OA\Schema(ref: '#/components/schemas/PromotionGiftNormalized'),
            new OA\Schema(ref: '#/components/schemas/GiftRequestNormalized'),
        ]),
    )]
    #[OA\Response(response: '409', description: 'Gift request path only: promotion conflict, body as promotion sent it')]
    #[OA\Response(response: '503', description: 'Gift request path only: promotion upstream unavailable, body as promotion sent it')]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route('/gift', name: 'promotion_gift_offer', methods: ['POST'])]
    public function postGift(
        int $domainId,
        int $playerId,
        Request $request,
        PermissionManager $permissionManager,
    ): JsonResponse|FormInterface {
        $permissionManager->denyAccessIfPermissionsNotGranted([
            OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_OFFER,
            OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_REQUEST,
        ]);
        $offers = $permissionManager->isPermissionsGranted([OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_OFFER]);

        $form = $this->createForm(OfferType::class);
        $form->submit($request->request->all());
        if (! $form->isValid()) {
            return $form;
        }

        $account = $this->memberZoneClient->getCustomerById($playerId);
        if (! $this->playerManager->isPlayerStatusValid($account['status'])) {
            $form->addError(new FormError(
                $this->translator->trans('player_status.status_invalid', ['%status%' => $account['status']])
            ));

            return $form;
        }

        /** @var User $user */
        $user = $this->getUser();

        if (! $offers) {
            return $this->requestGift($form, $user, $domainId, $playerId, $account['domain']['company_id'] ?? null);
        }

        $offerRequest = $this->giftNormalizer->normalizeOfferRequest($user, $form->getData());

        try {
            $gift = $this->promotionClient->offerGift($domainId, $playerId, $offerRequest);
        } catch (V2Exception $e) {
            if ($this->isValidationFailure($e)) {
                $this->formHelper->setFormErrorsFromArray(
                    $form,
                    $this->giftNormalizer->mapPromotionErrors($e->getErrors()),
                );

                return $form;
            }

            return $this->formHelper->handleV2Exception($e);
        }

        $this->userActivityJobManager->dispatchGiftOfferJob(
            $domainId,
            $playerId,
            $account['domain']['company_id'] ?? null,
            $gift,
        );

        return new JsonResponse($this->giftNormalizer->normalizeOne($domainId, $gift));
    }

    #[OA\Get(
        path: '/api/gateway/domain/{domainId}/player/{playerId}/gifts',
        summary: 'Gift list',
        tags: ['Gift'],
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\PathParameter(name: 'playerId', required: true, schema: new OA\Schema(type: 'integer'), example: 1)]
    #[OA\QueryParameter(
        name: 'limit',
        description: 'Sets the maximum number of results (rows) to return.',
        schema: new OA\Schema(type: 'integer', maximum: QueryType::MAX_LIMIT, minimum: 1, example: 100, nullable: true)
    )]
    #[OA\QueryParameter(ref: '#/components/parameters/query_offset')]
    #[OA\QueryParameter(
        name: 'order',
        schema: new OA\Schema(ref: '#/components/schemas/PromotionGiftOrder'),
        example: ['order[field]' => 'createdAt', 'order[direction]' => 'desc']
    )]
    #[OA\Response(response: '200', description: 'List of gifts', content: new OA\JsonContent(
        type: 'array',
        items: new OA\Items(ref: '#/components/schemas/PromotionGiftNormalized')
    ))]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route('/gifts', name: 'promotion_gift_list', methods: ['GET'])]
    public function getGifts(int $domainId, int $playerId, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted('ROLE_OAUTH2_PS_GIFT_LIST');

        $form = $this->createForm(QueryType::class);
        $form->submit($request->query->all());
        if (! $form->isValid()) {
            return $form;
        }

        $query = $this->giftNormalizer->normalizeRequest($form->getData(), $playerId);

        try {
            $gifts = $this->promotionClient->getGifts($domainId, $query);
        } catch (V2Exception $e) {
            return $this->formHelper->handleV2Exception($e);
        }

        return new JsonResponse($this->giftNormalizer->normalizeMany($domainId, $gifts));
    }

    private function requestGift(
        FormInterface $form,
        User $user,
        int $domainId,
        int $playerId,
        ?int $companyId,
    ): JsonResponse|FormInterface {
        try {
            $giftRequest = $this->promotionClient->postGiftRequest(
                $domainId,
                $playerId,
                $this->giftRequestNormalizer->normalizeCreateRequest($user, $form->getData()),
            );
        } catch (V2Exception $e) {
            return $this->handleGiftRequestException($e, $form);
        }

        $this->userActivityJobManager->dispatchGiftRequestedJob($companyId, $giftRequest);

        return new JsonResponse($this->giftRequestNormalizer->normalizeOne($giftRequest));
    }

    private function isValidationFailure(V2Exception $e): bool
    {
        $previous = $e->getPrevious();

        return $previous instanceof BadResponseException
            && $previous->getResponse()->getStatusCode() === Response::HTTP_BAD_REQUEST;
    }
}
