<?php

namespace App\GatewayBundle\Controller\Promotion;

use App\AppBundle\Helper\FormHelper;
use App\GatewayBundle\Form\Type\Promotion\GiftRequest\ApproveType;
use App\GatewayBundle\Form\Type\Promotion\GiftRequest\PlayerQueryType;
use App\GatewayBundle\Form\Type\Promotion\GiftRequest\QueryType;
use App\GatewayBundle\Form\Type\Promotion\GiftRequest\RejectType;
use App\GatewayBundle\Manager\PermissionManager;
use App\GatewayBundle\Manager\UserActivityJobManager;
use App\GatewayBundle\Normalizer\Promotion\GiftNormalizer;
use App\GatewayBundle\Normalizer\Promotion\GiftRequestNormalizer;
use App\Library\MemberZoneClient;
use App\Library\PromotionClient;
use App\OAuth2Bundle\Security\Authentication\OAuth2Authenticator;
use App\OAuth2Bundle\Security\User\User;
use CurlLibrary\Exception\V2Exception;
use OpenApi\Attributes as OA;
use Psr\Log\LoggerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\Form\FormInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

#[OA\Tag(name: 'Gift', description: 'Gift')]
class GiftRequestController extends AbstractController
{
    use GiftRequestErrorTrait;

    private const string PS_GIFT_LIST = 'PS_GIFT_LIST';
    private const string PS_GIFT_REQUEST_VALIDATE = 'PS_GIFT_REQUEST_VALIDATE';

    public function __construct(
        private readonly PromotionClient $promotionClient,
        private readonly GiftNormalizer $giftNormalizer,
        private readonly GiftRequestNormalizer $giftRequestNormalizer,
        private readonly FormHelper $formHelper,
        private readonly MemberZoneClient $memberZoneClient,
        private readonly UserActivityJobManager $userActivityJobManager,
        private readonly LoggerInterface $logger,
    ) {
    }

    #[OA\Get(
        path: '/api/gateway/domain/{domainId}/gift-requests',
        summary: 'Pending gift requests of the domain',
        tags: ['Gift'],
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\QueryParameter(name: 'filter', schema: new OA\Schema(ref: '#/components/schemas/PromotionGiftRequestFilter'))]
    #[OA\QueryParameter(
        name: 'limit',
        description: 'Sets the maximum number of results (rows) to return.',
        schema: new OA\Schema(type: 'integer', maximum: QueryType::MAX_LIMIT, minimum: 1, example: 100, nullable: true)
    )]
    #[OA\QueryParameter(ref: '#/components/parameters/query_offset')]
    #[OA\QueryParameter(
        name: 'order',
        schema: new OA\Schema(ref: '#/components/schemas/PromotionGiftRequestOrder'),
        example: ['order[field]' => 'requestedAt', 'order[direction]' => 'desc']
    )]
    #[OA\Response(response: '200', description: 'List of gift requests', content: new OA\JsonContent(
        type: 'array',
        items: new OA\Items(ref: '#/components/schemas/GiftRequestNormalized')
    ))]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route('/gift-requests', name: 'promotion_gift_request_domain_list', methods: ['GET'])]
    public function getDomainGiftRequests(int $domainId, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted(OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_REQUEST_VALIDATE);

        $form = $this->createForm(QueryType::class);
        $form->submit($request->query->all());
        if (! $form->isValid()) {
            return $form;
        }

        try {
            $requests = $this->promotionClient->getDomainGiftRequests(
                $domainId,
                $this->giftRequestNormalizer->normalizeListQuery($form->getData()),
            );
        } catch (V2Exception $e) {
            return $this->formHelper->handleV2Exception($e);
        }

        return new JsonResponse($this->giftRequestNormalizer->normalizeMany($requests));
    }

    #[OA\Get(
        path: '/api/gateway/domain/{domainId}/gift-requests/count',
        summary: 'Gift requests of the domain per status, for every filter except the status',
        tags: ['Gift'],
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\QueryParameter(name: 'filter', schema: new OA\Schema(ref: '#/components/schemas/PromotionGiftRequestFilter'))]
    #[OA\Response(response: '200', description: 'Count per status', content: new OA\JsonContent(
        properties: [
            new OA\Property(property: 'requested', type: 'integer'),
            new OA\Property(property: 'approved', type: 'integer'),
            new OA\Property(property: 'rejected', type: 'integer'),
        ],
        type: 'object',
    ))]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route('/gift-requests/count', name: 'promotion_gift_request_domain_count', methods: ['GET'])]
    public function countDomainGiftRequests(int $domainId, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted(OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_REQUEST_VALIDATE);

        $form = $this->createForm(QueryType::class);
        $form->submit($request->query->all());
        if (! $form->isValid()) {
            return $form;
        }

        try {
            $counts = $this->promotionClient->getDomainGiftRequestsCount(
                $domainId,
                $this->giftRequestNormalizer->normalizeListQuery($form->getData()),
            );
        } catch (V2Exception $e) {
            return $this->formHelper->handleV2Exception($e);
        }

        return new JsonResponse($counts);
    }

    #[OA\Get(
        path: '/api/gateway/domain/{domainId}/player/{playerId}/gift-requests',
        summary: 'Pending and recently rejected gift requests of the player',
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
        schema: new OA\Schema(ref: '#/components/schemas/PromotionPlayerGiftRequestOrder'),
        example: ['order[field]' => 'requestedAt', 'order[direction]' => 'desc']
    )]
    #[OA\Response(response: '200', description: 'List of gift requests', content: new OA\JsonContent(
        type: 'array',
        items: new OA\Items(ref: '#/components/schemas/GiftRequestNormalized')
    ))]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route('/player/{playerId}/gift-requests', name: 'promotion_gift_request_player_list', methods: ['GET'])]
    public function getPlayerGiftRequests(
        int $domainId,
        int $playerId,
        Request $request,
        PermissionManager $permissionManager,
    ): JsonResponse|FormInterface {
        $permissionManager->denyAccessIfPermissionsNotGranted([
            OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_LIST,
            OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_REQUEST_VALIDATE,
        ]);

        $form = $this->createForm(PlayerQueryType::class);
        $form->submit($request->query->all());
        if (! $form->isValid()) {
            return $form;
        }

        try {
            $requests = $this->promotionClient->getPlayerGiftRequests(
                $domainId,
                $playerId,
                $this->giftRequestNormalizer->normalizeListQuery($form->getData()),
            );
        } catch (V2Exception $e) {
            return $this->formHelper->handleV2Exception($e);
        }

        return new JsonResponse($this->giftRequestNormalizer->normalizeMany($requests));
    }

    #[OA\Post(
        path: '/api/gateway/domain/{domainId}/gift-request/{id}/approve',
        summary: 'Approve a gift request',
        tags: ['Gift'],
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\PathParameter(name: 'id', required: true, schema: new OA\Schema(type: 'integer'), example: 1)]
    #[OA\Response(
        response: '200',
        description: 'The gift created from the request',
        content: new OA\JsonContent(ref: '#/components/schemas/PromotionGiftNormalized'),
    )]
    #[OA\Response(response: '409', description: 'The request is not pending, body as promotion sent it')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[OA\Response(response: '404', description: 'Not found')]
    #[Route('/gift-request/{id}/approve', name: 'promotion_gift_request_approve', methods: ['POST'])]
    public function approve(int $domainId, int $id, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted(OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_REQUEST_VALIDATE);

        $form = $this->createForm(ApproveType::class);
        $form->submit($request->request->all());
        if (! $form->isValid()) {
            return $form;
        }

        /** @var User $user */
        $user = $this->getUser();

        try {
            $gift = $this->promotionClient->approveGiftRequest(
                $domainId,
                $id,
                $this->giftRequestNormalizer->normalizeApproveRequest($user, $form->getData()),
            );
        } catch (V2Exception $e) {
            return $this->handleGiftRequestException($e);
        }

        $normalized = $this->giftNormalizer->normalizeOne($domainId, $gift);
        $this->userActivityJobManager->dispatchGiftOfferJob(
            $gift['domainId'],
            $gift['playerId'],
            $this->resolveCompanyId($gift['playerId']),
            $gift,
            [
                'requested_by_name' => $normalized['requestedBy']['name'] ?? null,
                'approved_by_name' => $normalized['approvedBy']['name'] ?? null,
            ],
        );

        return new JsonResponse($normalized);
    }

    #[OA\Post(
        path: '/api/gateway/domain/{domainId}/gift-request/{id}/reject',
        summary: 'Reject a gift request',
        tags: ['Gift'],
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\PathParameter(name: 'id', required: true, schema: new OA\Schema(type: 'integer'), example: 1)]
    #[OA\RequestBody(required: true, content: new OA\JsonContent(ref: '#/components/schemas/GiftRequestRejectRequest'))]
    #[OA\Response(
        response: '200',
        description: 'The rejected gift request',
        content: new OA\JsonContent(ref: '#/components/schemas/GiftRequestNormalized'),
    )]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(response: '409', description: 'The request is not pending, body as promotion sent it')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[OA\Response(response: '404', description: 'Not found')]
    #[Route('/gift-request/{id}/reject', name: 'promotion_gift_request_reject', methods: ['POST'])]
    public function reject(int $domainId, int $id, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted(OAuth2Authenticator::ROLE_PREFIX . self::PS_GIFT_REQUEST_VALIDATE);

        $form = $this->createForm(RejectType::class);
        $form->submit($request->request->all());
        if (! $form->isValid()) {
            return $form;
        }

        /** @var User $user */
        $user = $this->getUser();

        try {
            $giftRequest = $this->promotionClient->rejectGiftRequest(
                $domainId,
                $id,
                $this->giftRequestNormalizer->normalizeRejectRequest($user, $form->getData()),
            );
        } catch (V2Exception $e) {
            return $this->handleGiftRequestException($e, $form);
        }

        $this->userActivityJobManager->dispatchGiftRequestRejectedJob(
            $this->resolveCompanyId($giftRequest['playerId']),
            $giftRequest,
        );

        return new JsonResponse($this->giftRequestNormalizer->normalizeOne($giftRequest));
    }

    private function resolveCompanyId(int $playerId): ?int
    {
        try {
            return $this->memberZoneClient->getCustomerById($playerId)['domain']['company_id'] ?? null;
        } catch (V2Exception $e) {
            $this->logger->error('Gift request player company lookup failed', [
                'player_id' => $playerId,
                'message' => $e->getMessage(),
            ]);

            return null;
        }
    }
}
