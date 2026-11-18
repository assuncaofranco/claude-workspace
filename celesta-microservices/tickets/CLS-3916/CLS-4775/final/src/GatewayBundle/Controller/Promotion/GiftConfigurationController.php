<?php

namespace App\GatewayBundle\Controller\Promotion;

use App\AppBundle\Helper\FormHelper;
use App\GatewayBundle\Form\Type\Promotion\Gift\RewardConfigurationGiftCountQueryType;
use App\GatewayBundle\Form\Type\Promotion\Gift\RewardConfigurationGiftQueryType;
use App\GatewayBundle\Form\Type\Promotion\RewardConfiguration\GiftRewardConfigurationType;
use App\GatewayBundle\Normalizer\Bonus\BonusModelNormalizer;
use App\GatewayBundle\Normalizer\Promotion\GiftNormalizer;
use App\Library\PromotionClient;
use CurlLibrary\Exception\V2Exception;
use OpenApi\Attributes as OA;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\Form\FormInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

#[OA\Tag(name: 'Reward configuration', description: 'Reward configuration')]
class GiftConfigurationController extends AbstractController
{
    public function __construct(
        private readonly PromotionClient $promotionClient,
        private readonly BonusModelNormalizer $normalizer,
        private readonly FormHelper $formHelper,
        private readonly GiftNormalizer $giftNormalizer,
    ) {
    }

    #[OA\Post(
        path: '/api/gateway/domain/{domainId}/reward_configuration/gift',
        summary: 'Create gift configuration',
        tags: ['Reward configuration']
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\RequestBody(
        required: true,
        content: new OA\JsonContent(ref: '#/components/schemas/RewardConfigurationGiftRequest')
    )]
    #[OA\Response(
        response: '200',
        description: 'Created gift configuration',
        content: new OA\JsonContent(ref: '#/components/schemas/BonusModelResponse')
    )]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route('/reward_configuration/gift', name: 'gift_configuration_post', methods: ['POST'])]
    public function postGiftConfigurationAction(int $domainId, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted('ROLE_OAUTH2_PS_BONUS_CONFIGURATION_CREATE');

        $form = $this->createForm(GiftRewardConfigurationType::class, null, ['domain_id' => $domainId]);
        $form->submit($request->request->all());
        if (! $form->isValid()) {
            return $form;
        }

        try {
            $giftConfiguration = $this->promotionClient->postRewardConfiguration(
                $domainId,
                $this->normalizer->normalizeGiftRequest($form->getData(), true),
            );
        } catch (V2Exception $ex) {
            return $this->formHelper->handleV2Exception($ex, $form, 'Error happens when trying to create gift');
        }

        return new JsonResponse($this->normalizer->normalize($giftConfiguration));
    }

    #[OA\Put(
        path: '/api/gateway/domain/{domainId}/reward_configuration/gift/{id}',
        summary: 'Edit gift configuration',
        tags: ['Reward configuration']
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\PathParameter(ref: '#/components/parameters/path_id')]
    #[OA\RequestBody(
        required: true,
        content: new OA\JsonContent(ref: '#/components/schemas/RewardConfigurationGiftRequest')
    )]
    #[OA\Response(
        response: '200',
        description: 'Edited gift configuration',
        content: new OA\JsonContent(ref: '#/components/schemas/BonusModelResponse')
    )]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route(
        path: '/reward_configuration/gift/{id}',
        name: 'gift_configuration_put',
        requirements: ['id' => '\d+'],
        methods: ['PUT']
    )]
    public function putGiftConfigurationAction(int $domainId, int $id, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted('ROLE_OAUTH2_PS_BONUS_CONFIGURATION_EDIT');

        $form = $this->createForm(GiftRewardConfigurationType::class, null, ['domain_id' => $domainId]);
        $form->submit($request->request->all());
        if (! $form->isValid()) {
            return $form;
        }

        try {
            $giftConfiguration = $this->promotionClient->patchRewardConfiguration(
                $domainId,
                $id,
                $this->normalizer->normalizeGiftRequest($form->getData(), false),
            );
        } catch (V2Exception $ex) {
            return $this->formHelper->handleV2Exception($ex, $form, 'Error happens when trying to edit gift');
        }

        return new JsonResponse($this->normalizer->normalize($giftConfiguration));
    }

    #[OA\Get(
        path: '/api/gateway/domain/{domainId}/gifts',
        summary: 'Gifts offered from reward configurations',
        tags: ['Reward configuration']
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\QueryParameter(
        name: 'limit',
        description: 'Sets the maximum number of results (rows) to return.',
        schema: new OA\Schema(
            type: 'integer',
            maximum: RewardConfigurationGiftQueryType::MAX_LIMIT,
            minimum: 1,
            example: 100,
            nullable: true,
        )
    )]
    #[OA\QueryParameter(ref: '#/components/parameters/query_offset')]
    #[OA\QueryParameter(
        name: 'order',
        schema: new OA\Schema(ref: '#/components/schemas/PromotionGiftOrder'),
        example: ['order[field]' => 'createdAt', 'order[direction]' => 'desc']
    )]
    #[OA\QueryParameter(
        name: 'filter',
        required: true,
        schema: new OA\Schema(ref: '#/components/schemas/RewardConfigurationGiftFilter')
    )]
    #[OA\Response(response: '200', description: 'List of gifts', content: new OA\JsonContent(
        type: 'array',
        items: new OA\Items(ref: '#/components/schemas/PromotionGiftNormalized')
    ))]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route('/gifts', name: 'reward_configuration_gift_list', methods: ['GET'])]
    public function getRewardConfigurationGiftsAction(int $domainId, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted('ROLE_OAUTH2_PS_BONUS_CONFIGURATION_LIST');

        $form = $this->createForm(RewardConfigurationGiftQueryType::class);
        $form->submit($request->query->all());
        if (! $form->isValid()) {
            return $form;
        }

        try {
            $gifts = $this->promotionClient->getGifts(
                $domainId,
                $this->giftNormalizer->normalizeRewardConfigurationRequest($form->getData()),
            );
        } catch (V2Exception $ex) {
            return $this->formHelper->handleV2Exception($ex);
        }

        return new JsonResponse($this->giftNormalizer->normalizeMany($domainId, $gifts));
    }

    #[OA\Get(
        path: '/api/gateway/domain/{domainId}/gifts/count',
        summary: 'Count of gifts offered from reward configurations',
        tags: ['Reward configuration']
    )]
    #[OA\PathParameter(ref: '#/components/parameters/path_domain_id')]
    #[OA\QueryParameter(ref: '#/components/parameters/query_count_aggregate')]
    #[OA\QueryParameter(
        name: 'filter',
        required: true,
        schema: new OA\Schema(ref: '#/components/schemas/RewardConfigurationGiftFilter')
    )]
    #[OA\Response(response: '200', description: 'Total gifts', content: new OA\JsonContent(properties: [
        new OA\Property(property: 'value', type: 'integer', example: 18),
    ]))]
    #[OA\Response(ref: '#/components/responses/validation-errors', response: '400')]
    #[OA\Response(ref: '#/components/responses/unauthorized', response: '401')]
    #[OA\Response(ref: '#/components/responses/access-denied', response: '403')]
    #[Route('/gifts/count', name: 'reward_configuration_gift_count', methods: ['GET'])]
    public function getRewardConfigurationGiftsCountAction(int $domainId, Request $request): JsonResponse|FormInterface
    {
        $this->denyAccessUnlessGranted('ROLE_OAUTH2_PS_BONUS_CONFIGURATION_COUNT');

        $form = $this->createForm(RewardConfigurationGiftCountQueryType::class);
        $form->submit($request->query->all());
        if (! $form->isValid()) {
            return $form;
        }

        try {
            $count = $this->promotionClient->getGiftsAggregate(
                $domainId,
                $this->giftNormalizer->normalizeRewardConfigurationRequest($form->getData()),
            );
        } catch (V2Exception $ex) {
            return $this->formHelper->handleV2Exception($ex);
        }

        return new JsonResponse(['value' => (int) $count]);
    }
}
