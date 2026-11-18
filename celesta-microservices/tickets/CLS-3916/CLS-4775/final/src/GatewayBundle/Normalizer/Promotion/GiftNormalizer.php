<?php

namespace App\GatewayBundle\Normalizer\Promotion;

use App\GatewayBundle\Normalizer\NormalizerTrait;
use App\Library\PromotionClient;
use App\UserBundle\Entity\User;
use App\UserBundle\Repository\UserRepository;
use CurlLibrary\Exception\V2Exception;
use Lancaster\Constants\Promotion\GiftConstants;
use OpenApi\Attributes as OA;
use Psr\Log\LoggerInterface;
use Symfony\Component\Security\Core\User\UserInterface;

class GiftNormalizer
{
    use NormalizerTrait;

    private const int DEFAULT_LIMIT = 100;
    private const int DEFAULT_OFFSET = 0;
    private const array USER_ID_KEYS = ['sourceUserId', 'requestedByUserId', 'approvedByUserId'];

    public function __construct(
        private readonly UserRepository $userRepository,
        private readonly PromotionClient $promotionClient,
        private readonly LoggerInterface $logger,
    ) {
    }

    public function normalizeOfferRequest(UserInterface $user, array $data): array
    {
        return [
            'rewardConfigurationId' => $data['rewardConfigurationId'],
            'amount' => isset($data['value']) ? (string) $data['value'] : null,
            'description' => $data['description'] ?? null,
            'reasonId' => $data['reasonId'] ?? null,
            'sourceUserId' => $user->getId(),
        ];
    }

    public function normalizeRequest(array $formData, int $playerId): array
    {
        $formData['limit'] ??= self::DEFAULT_LIMIT;
        $formData['offset'] ??= self::DEFAULT_OFFSET;

        return $this->normalizeQueryRequest($formData, [
            'filter' => ['ownerIds' => [$playerId]],
        ]);
    }

    public function normalizeRewardConfigurationRequest(array $formData): array
    {
        if (empty($formData['aggregate'])) {
            $formData['limit'] ??= self::DEFAULT_LIMIT;
            $formData['offset'] ??= self::DEFAULT_OFFSET;
        }

        return $this->normalizeQueryRequest($formData, [
            'filter' => ['rewardConfigurationIds' => $formData['filter']['rewardConfigurationIds']],
        ]);
    }

    public function normalizeOne(int $domainId, array $gift): array
    {
        return $this->normalize(
            $gift,
            $this->resolveUsers([$gift]),
            $this->resolvePromotionConfigurations($domainId, [$gift]),
        );
    }

    public function normalizeMany(int $domainId, array $gifts): array
    {
        $users = $this->resolveUsers($gifts);
        $promotionConfigurations = $this->resolvePromotionConfigurations($domainId, $gifts);

        return array_map(
            fn (array $gift): array => $this->normalize($gift, $users, $promotionConfigurations),
            $gifts,
        );
    }

    #[OA\Schema(
        schema: 'GiftCreatedBy',
        description: 'The BO user who recorded the gift, or the promotion configuration that offered it. Null for a scenario gift or a source that no longer resolves.',
        properties: [
            new OA\Property(property: 'id', type: 'integer', example: 1),
            new OA\Property(property: 'name', type: 'string', example: 'Marta Kulas'),
        ],
        type: 'object',
        nullable: true,
    )]
    #[OA\Schema(
        schema: 'GiftRequestUser',
        description: 'A BO user. Null when promotion has none or the user no longer resolves.',
        properties: [
            new OA\Property(property: 'id', type: 'integer', example: 1),
            new OA\Property(property: 'name', type: 'string', example: 'Marta Kulas'),
        ],
        type: 'object',
        nullable: true,
    )]
    #[OA\Schema(
        schema: 'PromotionGiftNormalized',
        title: 'Promotion Gift',
        properties: [
            new OA\Property(property: 'id', type: 'integer', example: 1),
            new OA\Property(property: 'playerId', type: 'integer', example: 1),
            new OA\Property(
                property: 'status',
                type: 'string',
                enum: GiftConstants::STATUSES,
                example: GiftConstants::STATUS_CLAIMED,
            ),
            new OA\Property(property: 'name', type: 'string', example: 'Birthday hamper'),
            new OA\Property(property: 'value', type: 'string', example: '150.50'),
            new OA\Property(property: 'currency', type: 'string', example: 'EUR'),
            new OA\Property(property: 'rewardConfigurationId', type: 'integer', example: 1, nullable: true),
            new OA\Property(
                property: 'description',
                type: 'string',
                example: 'Handed over at the VIP dinner',
                nullable: true,
            ),
            new OA\Property(property: 'reasonId', type: 'integer', example: 1, nullable: true),
            new OA\Property(
                property: 'reason',
                description: 'Name of the gift\'s reason, deleted reasons included.',
                type: 'string',
                example: 'Birthday',
                nullable: true,
            ),
            new OA\Property(property: 'createdBy', ref: '#/components/schemas/GiftCreatedBy'),
            new OA\Property(
                property: 'sourceScenarioId',
                description: 'The scenario that offered the gift. Null when a BO user recorded it.',
                type: 'integer',
                example: 12,
                nullable: true,
            ),
            new OA\Property(
                property: 'sourcePromotionId',
                description: 'The promotion configuration that offered the gift. Null when a BO user or a scenario recorded it.',
                type: 'integer',
                example: 5,
                nullable: true,
            ),
            new OA\Property(property: 'createdAt', type: 'string', example: '2026-09-22 11:07:20'),
            new OA\Property(property: 'updatedAt', type: 'string', example: '2026-09-22 11:07:20', nullable: true),
            new OA\Property(
                property: 'giftRequestId',
                description: 'The request the gift was approved from. Null for a gift offered directly.',
                type: 'integer',
                example: 12,
                nullable: true,
            ),
            new OA\Property(property: 'requestedAt', type: 'string', example: '2026-09-22 10:00:00', nullable: true),
            new OA\Property(property: 'approvedAt', type: 'string', example: '2026-09-22 11:07:20', nullable: true),
            new OA\Property(property: 'requestedBy', ref: '#/components/schemas/GiftRequestUser'),
            new OA\Property(property: 'approvedBy', ref: '#/components/schemas/GiftRequestUser'),
        ]
    )]
    public function normalize(array $gift, array $users = [], ?array $promotionConfigurations = []): array
    {
        return [
            'id' => $gift['id'],
            'playerId' => $gift['playerId'] ?? null,
            'status' => $gift['status'],
            'name' => $gift['name'],
            'value' => $gift['amount'],
            'currency' => $gift['currency'],
            'rewardConfigurationId' => $gift['rewardConfigurationId'] ?? null,
            'description' => $gift['description'] ?? null,
            'reasonId' => $gift['reasonId'] ?? null,
            'reason' => $gift['reasonName'] ?? null,
            'createdBy' => $this->normalizeCreatedBy($gift, $users, $promotionConfigurations),
            'sourceScenarioId' => $gift['sourceScenarioId'] ?? null,
            'sourcePromotionId' => $gift['sourcePromotionId'] ?? null,
            'createdAt' => $gift['createdAt'] ?? null,
            'updatedAt' => $gift['updatedAt'] ?? null,
            'giftRequestId' => $gift['giftRequestId'] ?? null,
            'requestedAt' => $gift['requestedAt'] ?? null,
            'approvedAt' => $gift['approvedAt'] ?? null,
            'requestedBy' => $this->normalizeUser($gift, 'requestedByUserId', $users),
            'approvedBy' => $this->normalizeUser($gift, 'approvedByUserId', $users),
        ];
    }

    public function mapPromotionErrors(array $errors): array
    {
        if (isset($errors['children']) && is_array($errors['children'])) {
            $errors['children'] = $this->renameErrorKey($errors['children'], 'amount', 'value');
        }

        if (isset($errors['errors']) && is_array($errors['errors'])) {
            $errors['errors'] = $this->mapPromotionErrors($errors['errors']);
        }

        return $this->renameErrorKey($errors, 'amount', 'value');
    }

    /**
     * @param list<string> $keys
     *
     * @return array<int, User> indexed by user id
     */
    public function resolveUsers(array $rows, array $keys = self::USER_ID_KEYS): array
    {
        $ids = [];
        foreach ($keys as $key) {
            foreach (array_column($rows, $key) as $id) {
                if ($id !== null) {
                    $ids[$id] = $id;
                }
            }
        }

        if ($ids === []) {
            return [];
        }

        $users = [];
        foreach ($this->userRepository->getUsersByIds(array_values($ids)) as $user) {
            $users[$user->getId()] = $user;
        }

        return $users;
    }

    public function normalizeUser(array $row, string $key, array $users): ?array
    {
        $userId = $row[$key] ?? null;

        if ($userId === null) {
            return null;
        }

        $user = $users[$userId] ?? null;
        if ($user === null) {
            $this->logger->error('Gift user does not resolve to a BO user', [
                'gift_id' => $row['id'] ?? null,
                'field' => $key,
                'user_id' => $userId,
            ]);

            return null;
        }

        return [
            'id' => $user->getId(),
            'name' => $user->getFullName(),
        ];
    }

    /**
     * @return array<int, array>|null promotion configurations indexed by id, null when the lookup failed
     */
    private function resolvePromotionConfigurations(int $domainId, array $gifts): ?array
    {
        $ids = array_values(array_unique(array_filter(
            array_column($gifts, 'sourcePromotionId'),
            static fn ($id): bool => $id !== null
        )));

        if ($ids === []) {
            return [];
        }

        try {
            $configurations = $this->promotionClient->getPromotionConfigurations($domainId, [
                'filter' => ['ids' => $ids],
                'limit' => count($ids),
                'offset' => 0,
            ]);
        } catch (V2Exception) {
            $this->logger->error('Gift source promotions could not be fetched', [
                'source_promotion_ids' => $ids,
            ]);

            return null;
        }

        return array_column($configurations, null, 'id');
    }

    private function normalizeCreatedBy(array $gift, array $users, ?array $promotionConfigurations): ?array
    {
        if (($gift['sourceUserId'] ?? null) !== null) {
            return $this->normalizeUser($gift, 'sourceUserId', $users);
        }

        $promotionId = $gift['sourcePromotionId'] ?? null;

        if ($promotionId === null || $promotionConfigurations === null) {
            return null;
        }

        $configuration = $promotionConfigurations[$promotionId] ?? null;
        if ($configuration === null) {
            $this->logger->error('Gift source promotion does not resolve to a promotion configuration', [
                'gift_id' => $gift['id'] ?? null,
                'source_promotion_id' => $promotionId,
            ]);

            return null;
        }

        return [
            'id' => $configuration['id'],
            'name' => $configuration['name'],
        ];
    }
}
