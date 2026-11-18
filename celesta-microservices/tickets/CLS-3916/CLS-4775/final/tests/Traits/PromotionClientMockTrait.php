<?php

namespace Tests\Traits;

use Lancaster\Constants\Currency\Currency;
use Lancaster\Constants\Promotion\PromotionConfigurationConstants;
use Lancaster\Constants\Promotion\RewardAggregatorConstants;
use Lancaster\Constants\Promotion\RewardConfigurationConstants;
use Lancaster\Constants\Promotion\RewardConstants;
use Lancaster\Constants\Wallet\BonusConstants;

trait PromotionClientMockTrait
{
    use BaseClientMockTrait;

    private const string PROMOTION_HOST = 'http://promotionweb.docker';

    private const array REWARD_TYPE_TO_REWARD_CONFIGURATION_TYPE = [
        RewardConstants::TYPE_FUTURE_DEPOSIT => RewardConfigurationConstants::TYPE_DEPOSIT,
        RewardConstants::TYPE_MATCH_DEPOSIT => RewardConfigurationConstants::TYPE_FREE,
        RewardConstants::TYPE_FREE_BONUS => RewardConfigurationConstants::TYPE_FREE,
        RewardConstants::TYPE_FREE_ROUND => RewardConfigurationConstants::TYPE_FREE_ROUNDS,
    ];

    protected static array $baseSingleMockPromotionConfiguration = [
        'id' => 1,
        'name' => 'Promotion name 1',
        'currency' => 'EUR',
        'status' => 'enabled',
        'startDate' => '2024-07-30 06:26:44',
        'endDate' => '2024-08-30 06:26:44',
        'segmentIds' => [1, 10],
        'engagementModel' => 'manual',
        'type' => PromotionConfigurationConstants::TYPE_DEPOSIT_TIER,
        'thumbnail' => 'https://cdn.test-assets.com/promotion/promotion-configuration/1/1/test_image.png',
        'engagementCode' => 'WELCOME2025',
    ];

    protected static array $baseListMockPromotionConfiguration = [
        'id' => 1,
        'domainId' => 1,
        'name' => 'Promotion name 1',
        'currency' => 'EUR',
        'status' => 'enabled',
        'engagementModel' => 'manual',
        'createdAt' => '2024-07-30 06:26:44',
        'updatedAt' => '2024-07-30 06:26:44',
        'startDate' => '2024-07-30 06:26:44',
        'endDate' => '2024-08-30 06:26:44',
        'segmentIds' => [1, 10],
        'type' => PromotionConfigurationConstants::TYPE_DEPOSIT_TIER,
        'rewardingLimit' => 20,
        'rewardCount' => 0,
        'playerPromotionLimit' => 5,
        'thumbnail' => 'https://cdn.test-assets.com/promotion/promotion-configuration/1/1/test_image.png',
        'engagementCode' => 'WELCOME2025',
    ];

    protected static array $baseMockPromotion = [
        'id' => 1,
        'player_id' => 1,
        'status' => 'engaged',
        'engaged_at' => '2024-07-30 06:26:44',
        'promotion_configuration_id' => 1,
        'created_at' => '2024-07-30 06:26:44',
        'updated_at' => '2024-07-30 06:26:44',
    ];

    protected static array $baseMockReward = [
        'id' => 1,
        'type' => RewardConstants::TYPE_FUTURE_DEPOSIT,
        'bonusModelId' => 1,
        'quantity' => 0.2,
        'options' => ['upToAmount' => 20],
    ];

    protected static array $basePromotionScheduleMock = [
        'id' => 1,
        'firstOccurrence' => [
            'startsAt' => '2025-03-03 13:18:53',
            'endsAt' => '2025-03-03 15:18:53',
        ],
        'recurrence' => [
            'type' => 'weekly',
            'interval' => 2,
            'daysOfWeek' => ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'],
        ],
        'finishCondition' => [
            'type' => 'date',
            'finishDate' => null,
        ],
        'engagementScope' => 'global',
    ];

    protected static array $basePromotionScheduleDailyMock = [
        'id' => 1,
        'firstOccurrence' => [
            'startsAt' => '2025-03-03 13:18:53',
            'endsAt' => '2025-03-03 15:18:53',
        ],
        'recurrence' => [
            'type' => 'monthly',
            'interval' => 2,
        ],
        'finishCondition' => [
            'type' => 'date',
            'finishDate' => null,
        ],
        'engagementScope' => 'global',
    ];

    protected static array $basePromotionScheduleWeeklyMock = [
        'id' => 1,
        'firstOccurrence' => [
            'startsAt' => '2025-03-03 13:18:53',
            'endsAt' => '2025-03-03 15:18:53',
        ],
        'recurrence' => [
            'type' => 'weekly',
            'interval' => 2,
            'daysOfWeek' => ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'],
        ],
        'finishCondition' => [
            'type' => 'date',
            'finishDate' => null,
        ],
        'engagementScope' => 'global',
    ];

    protected static array $basePromotionScheduleMonthlyMock = [
        'id' => 1,
        'firstOccurrence' => [
            'startsAt' => '2025-03-03 13:18:53',
            'endsAt' => '2025-03-03 15:18:53',
        ],
        'recurrence' => [
            'type' => 'monthly',
            'interval' => 2,
        ],
        'finishCondition' => [
            'type' => 'date',
            'finishDate' => null,
        ],
        'engagementScope' => 'global',
    ];

    protected static array $basePromotionScheduleYearlyMock = [
        'id' => 1,
        'firstOccurrence' => [
            'startsAt' => '2025-03-03 13:18:53',
            'endsAt' => '2025-03-03 15:18:53',
        ],
        'recurrence' => [
            'type' => 'yearly',
            'interval' => 2,
        ],
        'finishCondition' => [
            'type' => 'date',
            'finishDate' => null,
        ],
        'engagementScope' => 'global',
    ];

    protected static array $baseRewardAggregator = [
        'id' => 1,
        'type' => RewardAggregatorConstants::TYPE_BET_RESULT,
        'options' => [
            'betResultEvent' => 'win',
        ],
        'rewards' => [
            [
                'id' => 1,
                'type' => 'match_deposit',
                'bonusModelId' => 1,
                'quantity' => 1,
            ],
        ],
        'createdAt' => '2024-07-30 06:26:44',
        'updatedAt' => '2024-07-30 06:26:44',
    ];

    protected static array $baseMockPromotionTag = [
        'id' => 1,
        'name' => 'Promotion Tag 1',
        'backgroundColor' => '#9fc06f',
        'domainId' => 1,
        'createdAt' => '2024-07-30 06:26:44',
        'updatedAt' => '2024-07-30 06:26:44',
        'promotionConfigurationIds' => [1, 2],
    ];

    protected static array $baseRewardAggregatorDepositTier = [
        'id' => 1,
        'type' => RewardAggregatorConstants::TYPE_TIER,
        'options' => [
            'minAmount' => 0,
            'maxAmount' => 100.50,
        ],
        'rewards' => [
            [
                'id' => 1,
                'type' => 'match_deposit',
                'bonusModelId' => 1,
                'quantity' => 1,
            ],
        ],
        'createdAt' => '2024-07-30 06:26:44',
        'updatedAt' => '2024-07-30 06:26:44',
    ];

    protected static array $baseRewardAggregatorMultiplusTier = [
        'id' => 1,
        'type' => RewardAggregatorConstants::TYPE_MULTIPLUS_TIER,
        'options' => [
            'minSelections' => 3,
            'maxSelections' => 10,
        ],
        'rewards' => [
            [
                'id' => 1,
                'type' => 'free_bonus',
                'bonusModelId' => 1,
                'quantity' => 10,
                'options' => [
                    'upToAmount' => 5.00,
                ],
            ],
        ],
        'createdAt' => '2024-12-10 06:26:44',
        'updatedAt' => '2024-12-10 06:26:44',
    ];

    protected static array $baseRewardAggregatorRafReferrer = [
        'id' => 1,
        'type' => RewardAggregatorConstants::TYPE_RAF_ROLE,
        'options' => [
            'role' => RewardAggregatorConstants::ROLE_REFERRER,
        ],
        'rewards' => [
            [
                'id' => 1,
                'type' => 'future_deposit',
                'bonusModelId' => 1,
            ],
        ],
    ];

    protected static array $baseRewardAggregatorRafReferee = [
        'id' => 1,
        'type' => RewardAggregatorConstants::TYPE_RAF_ROLE,
        'options' => [
            'role' => RewardAggregatorConstants::ROLE_REFEREE,
        ],
        'rewards' => [
            [
                'id' => 1,
                'type' => 'free_bonus',
                'bonusModelId' => 1,
                'quantity' => 10,
            ],
        ],
    ];

    public static function mockGetPromotionConfigurations(): void
    {
        $firstConfig = self::resolvePromotionConfiguration(PromotionConfigurationConstants::TYPE_DEPOSIT_TIER, true);
        $secondConfig = array_merge(
            self::resolvePromotionConfiguration(PromotionConfigurationConstants::TYPE_FIRST_BET_INSURANCE, true),
            ['id' => 2, 'name' => 'First bet insurance'],
        );
        $thirdConfig = array_merge(
            self::resolvePromotionConfiguration(PromotionConfigurationConstants::TYPE_REFER_FRIEND, true),
            ['id' => 3, 'name' => 'Refer a friend'],
        );

        $data = [
            $firstConfig,
            $secondConfig,
            $thirdConfig,
        ];

        self::mockMethod('GET', self::PROMOTION_HOST . '/api/domain/1/promotion-configurations', 200, json_encode($data));
    }

    public static function mockGetPromotionConfigurationsCount(): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configurations/count',
            200,
            100
        );
    }

    public static function mockGetPromotionConfiguration(
        string $type = PromotionConfigurationConstants::TYPE_DEPOSIT_TIER,
        int $domainId = 1,
        int $promotionConfigurationId = 1,
    ): void {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/{$domainId}/promotion-configuration/{$promotionConfigurationId}",
            200,
            json_encode(self::resolvePromotionConfiguration($type))
        );
    }

    public static function mockPatchPromotionConfiguration(
        string $type = PromotionConfigurationConstants::TYPE_DEPOSIT_TIER,
    ): void {
        self::mockMethod(
            'PATCH',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1',
            200,
            json_encode(self::resolvePromotionConfiguration($type))
        );
    }

    public static function mockPostPromotionConfiguration(
        string $type = PromotionConfigurationConstants::TYPE_DEPOSIT_TIER,
    ): void {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration',
            200,
            json_encode(self::resolvePromotionConfiguration($type))
        );
    }

    public static function mockGetPromotions(): void
    {
        $data = [
            self::$baseMockPromotion,
            array_merge(self::$baseMockPromotion, [
                'id' => 2,
                'player_id' => 2,
            ]),
        ];

        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/promotions',
            200,
            json_encode($data)
        );
    }

    public static function mockGetPromotionsCount(int $count = 10): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/promotions/count',
            200,
            json_encode($count)
        );
    }

    public static function mockPostReward(string $type = RewardConstants::TYPE_FUTURE_DEPOSIT): void
    {
        $data = self::$baseMockReward;
        $data['type'] = $type;

        if (in_array($type, [
            RewardConstants::TYPE_MATCH_DEPOSIT,
            RewardConstants::TYPE_FREE_ROUND,
            RewardConstants::TYPE_MATCH_BET,
        ])) {
            $data['quantity'] = 20;
        }

        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward',
            200,
            json_encode($data),
        );

        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward-aggregator/1/reward',
            200,
            json_encode($data)
        );
    }

    public static function mockPatchReward(): void
    {
        self::mockMethod(
            'PATCH',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward/1',
            200,
            json_encode(self::$baseMockReward),
        );
    }

    public static function mockDeleteReward(): void
    {
        self::mockMethod(
            'DELETE',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward/1',
            204,
            '{}',
        );

        self::mockMethod(
            'DELETE',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward-aggregator/1/reward/1',
            204,
            '{}',
        );
    }

    public static function mockGetReward(string $type): void
    {
        $data = self::$baseMockReward;
        $data['type'] = $type;

        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward/1',
            200,
            json_encode($data),
        );
    }

    public static function mockGetRewards(string $type = RewardConstants::TYPE_FREE_BONUS, int $domainId = 1, int $rewardConfigurationId = 1): void
    {
        $data = [
            array_merge(self::$baseMockReward, ['type' => $type]),
        ];

        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/promotion-configuration/$rewardConfigurationId/rewards",
            200,
            json_encode($data),
        );
    }

    public static function mockGetOfferableRewardConfigurationForReward(
        ?string $rewardType,
        int $domainId = 1,
        int $rewardConfigurationId = 1,
    ): void {
        $type = self::REWARD_TYPE_TO_REWARD_CONFIGURATION_TYPE[$rewardType] ?? null;
        if ($type === null) {
            return;
        }

        $data = self::rewardConfigurationData($type, $domainId, $rewardConfigurationId);
        $data['offeringMethod'] = RewardConfigurationConstants::OFFERING_METHOD_MANUAL;

        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/reward-configuration/$rewardConfigurationId",
            200,
            json_encode($data),
        );
    }

    private static function rewardConfigurationData(string $type, int $domainId, int $rewardConfigurationId): array
    {
        return [
            'id' => $rewardConfigurationId,
            'domainId' => $domainId,
            'name' => 'Test Reward Configuration',
            'displayName' => 'Display name',
            'type' => $type,
            'model' => RewardConfigurationConstants::MODEL_UPPER,
            'offeringMethod' => RewardConfigurationConstants::OFFERING_METHOD_AUTOMATIC,
            'offerAmount' => '39.00',
            'wageringMultiplier' => null,
            'status' => RewardConfigurationConstants::STATUS_ENABLED,
            'recurrence' => 'weekly',
            'offeringStatus' => 'inactive',
            'offerPeriodFrom' => null,
            'offerPeriodTo' => null,
            'recurrenceDailyFrom' => null,
            'recurrenceDailyTo' => null,
            'recurrenceWeeklyFrom' => 'Monday 22:11',
            'recurrenceWeeklyTo' => 'Monday 23:11',
            'recurrenceMonthlyFrom' => null,
            'recurrenceMonthlyTo' => null,
            'offerValidFor' => null,
            'validDuringDays' => 3,
            'occurrences' => 10,
            'segmentIds' => [],
            'maxWinMultiplier' => null,
            'offerPercent' => null,
            'offerUpToAmount' => null,
            'createdAt' => '2026-02-04 15:19:56',
            'deletedAt' => null,
            'offerEndAt' => null,
            'currency' => Currency::EUR,
            'reason' => RewardConfigurationConstants::REASON_TEST,
            'offerDescription' => '39',
            'freeRoundConfiguration' => null,
            'promotionId' => null,
            'claimingEventCondition' => null,
            'claimingEvent' => RewardConfigurationConstants::CLAIMING_EVENT_DIRECT,
            'gameplayRestrictionGameIds' => [],
            'thumbnail' => null,
        ];
    }

    public static function mockOfferReward(int $domainId = 1, int $playerId = 1, int $rewardConfigurationId = 1): void
    {
        $data = [
            'id' => 21,
            'status' => 'offered',
            'playerId' => $playerId,
            'validityPeriodTo' => null,
            'amount' => 10.1,
            'wageringMultiplier' => 3.0,
        ];

        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/player/$playerId/reward-configuration/$rewardConfigurationId/offer",
            200,
            json_encode($data),
        );
    }

    public static function mockGetRewardingByDomain(int $domainId = 1, array $response = []): void
    {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST."/api/domain/$domainId/rewarding",
            200,
            json_encode($response),
        );
    }

    public static function mockGetPromotionConfigurationSchedules(
        int $domainId = 1,
        int $promotionConfigurationId = 1,
    ): void {
        $uri = self::PROMOTION_HOST . "/api/domain/$domainId/promotion-configuration/$promotionConfigurationId/schedules";

        self::mockMethod(
            'GET',
            $uri,
            200,
            json_encode([self::$basePromotionScheduleMock]),
        );
    }

    public static function mockPostPromotionSchedule(int $domainId = 1, int $configurationId = 1, $recurrence = 'weekly'): void
    {
        $promotionScheduleMock = self::getRecurrenceDataMock($recurrence);

        $uri = self::PROMOTION_HOST . "/api/domain/$domainId/promotion-configuration/$configurationId/schedule";

        self::mockMethod(
            'POST',
            $uri,
            200,
            json_encode($promotionScheduleMock),
        );
    }

    public static function getRecurrenceDataMock(string $recurrence)
    {
        switch ($recurrence) {
            case 'daily':
                return self::$basePromotionScheduleDailyMock;
            case 'monthly':
                return self::$basePromotionScheduleMonthlyMock;
            case 'yearly':
                return self::$basePromotionScheduleYearlyMock;
            default:
                return self::$basePromotionScheduleWeeklyMock;
        }
    }

    public static function mockPutPromotionSchedule(
        int $domainId = 1,
        int $configurationId = 1,
        int $scheduleId = 1,
    ): void {
        $uri = sprintf(
            '%s/api/domain/%s/promotion-configuration/%s/schedule/%s',
            self::PROMOTION_HOST,
            $domainId,
            $configurationId,
            $scheduleId
        );

        self::mockMethod(
            'PUT',
            $uri,
            200,
            json_encode(self::$basePromotionScheduleMock),
        );
    }

    public static function mockDeletePromotionSchedule(
        int $domainId = 1,
        int $configurationId = 1,
        int $scheduleId = 1,
    ): void {
        $uri = sprintf(
            '%s/api/domain/%s/promotion-configuration/%s/schedule/%s',
            self::PROMOTION_HOST,
            $domainId,
            $configurationId,
            $scheduleId
        );

        self::mockMethod('DELETE', $uri, 204, '{}');
    }

    public static function mockGetRewardAggregators(): void
    {
        $data = [
            self::$baseRewardAggregator,
            array_merge(self::$baseRewardAggregator, ['id' => 2]),
        ];

        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward-aggregators',
            200,
            json_encode($data),
        );
    }

    public static function mockPostRewardsAggregator(string $promoConfigType = '', ?string $rafRole = null): void
    {
        $data = self::$baseRewardAggregator;

        if ($promoConfigType === PromotionConfigurationConstants::TYPE_DEPOSIT_TIER) {
            $data = self::$baseRewardAggregatorDepositTier;
        } elseif ($promoConfigType === PromotionConfigurationConstants::TYPE_MULTIPLUS) {
            $data = self::$baseRewardAggregatorMultiplusTier;
        } elseif ($promoConfigType === PromotionConfigurationConstants::TYPE_REFER_FRIEND) {
            if ($rafRole === RewardAggregatorConstants::ROLE_REFERRER) {
                $data = self::$baseRewardAggregatorRafReferrer;
            } elseif ($rafRole === RewardAggregatorConstants::ROLE_REFEREE) {
                $data = self::$baseRewardAggregatorRafReferee;
            }
        }

        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward-aggregators',
            200,
            json_encode([$data]),
        );
    }

    public static function mockPatchRewardAggregator(string $aggregatorType = RewardAggregatorConstants::TYPE_BET_RESULT): void
    {
        $data = self::$baseRewardAggregator;

        if ($aggregatorType === RewardAggregatorConstants::TYPE_TIER) {
            $data = self::$baseRewardAggregatorDepositTier;
        } elseif ($aggregatorType === RewardAggregatorConstants::TYPE_MULTIPLUS_TIER) {
            $data = self::$baseRewardAggregatorMultiplusTier;
        }

        self::mockMethod(
            'PATCH',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward-aggregator/1',
            200,
            json_encode($data),
        );
    }

    public static function mockDeleteRewardAggregator(): void
    {
        self::mockMethod(
            'DELETE',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/reward-aggregator/1',
            204,
            '{}',
        );
    }

    public static function mockValidatePromotionScheduleSuccess(int $domainId = 1): void
    {
        $uri = self::PROMOTION_HOST . "/api/domain/$domainId/schedule/validate";

        self::mockMethod(
            'POST',
            $uri,
            200,
            '{"success": true}',
        );
    }

    public static function mockValidatePromotionScheduleFailure(int $domainId = 1): void
    {
        $mockData = [
            'message' => 'Validation Failed',
            'errors' => [
                'firstOccurrence' => [
                    'startsAt' => ['This value should not be blank.'],
                    'endsAt' => ['This value should not be blank.'],
                ],
            ],
        ];

        $uri = self::PROMOTION_HOST . "/api/domain/$domainId/schedule/validate";

        self::mockMethod(
            'POST',
            $uri,
            400,
            json_encode($mockData),
        );
    }

    public static function mockGetPromotionTags(): void
    {
        $data = [
            self::$baseMockPromotionTag,
            array_merge(self::$baseMockPromotionTag, [
                'id' => 2,
                'name' => 'Promotion Tag 2',
                'backgroundColor' => '#ff5733',
                'domainId' => 1,
                'createdAt' => '2024-07-30 06:26:44',
                'updatedAt' => '2024-07-30 06:26:44',
            ]),
        ];

        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . '/api/domain/1/promotion-tags',
            200,
            json_encode($data)
        );
    }

    public static function mockGetPromotionTagsCount(int $count = 10): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . '/api/domain/1/promotion-tags/count',
            200,
            json_encode($count)
        );
    }

    public static function mockPostPromotionTag(): void
    {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . '/api/domain/1/promotion-tag',
            200,
            json_encode(self::$baseMockPromotionTag)
        );
    }

    public static function mockPatchPromotionTag(): void
    {
        self::mockMethod(
            'PATCH',
            self::PROMOTION_HOST . '/api/domain/1/promotion-tag/1',
            200,
            json_encode(self::$baseMockPromotionTag)
        );
    }

    public static function mockDeletePromotionTag(): void
    {
        self::mockMethod(
            'DELETE',
            self::PROMOTION_HOST . '/api/domain/1/promotion-tag/1',
            204,
            '{}'
        );
    }

    public function mockAddTagsToPromotionConfiguration(): void
    {
        $tagsResponse = [
            [
                'domainId' => 1,
                'tagId' => 1,
                'promotionConfigurationId' => 1,
            ],
            [
                'domainId' => 1,
                'tagId' => 2,
                'promotionConfigurationId' => 1,
            ],
        ];

        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/tags',
            200,
            json_encode($tagsResponse)
        );
    }

    protected function mockReplaceTagsInPromotionConfiguration(): void
    {
        $tagsResponse = [
            [
                'domainId' => 1,
                'tagId' => 3,
                'promotionConfigurationId' => 1,
            ],
            [
                'domainId' => 1,
                'tagId' => 4,
                'promotionConfigurationId' => 1,
            ],
        ];

        self::mockMethod(
            'PUT',
            self::PROMOTION_HOST . '/api/domain/1/promotion-configuration/1/tags',
            200,
            json_encode($tagsResponse)
        );
    }

    public static function mockPostRewardConfigurationFreeWagerDaily(): void
    {
        $mockData = [
            'id' => 11,
            'name' => 'asd',
            'displayName' => '',
            'type' => RewardConfigurationConstants::TYPE_FREE,
            'model' => RewardConfigurationConstants::MODEL_WAGER,
            'status' => RewardConfigurationConstants::STATUS_DISABLED,
            'reason' => null,
            'currency' => Currency::EUR,
            'offeringMethod' => RewardConfigurationConstants::OFFERING_METHOD_AUTOMATIC,
            'occurrences' => 1,
            'offerAmount' => 1,
            'wageringMultiplier' => 1,
            'maxWinMultiplier' => 1,
            'validDuringDays' => 1,
            'createdAt' => '2021-11-30 16:38:38',
            'segmentIds' => [1],
            'claimingEvent' => RewardConfigurationConstants::CLAIMING_EVENT_DIRECT,
            'claimingEventCondition' => null,
            'gameplayRestrictionGameIds' => [],
            'thumbnail' => null,
            'recurrence' => RewardConfigurationConstants::RECURRENCE_DAILY,
            'offerPeriodFrom' => null,
            'offerPeriodTo' => null,
            'recurrenceDailyFrom' => '13:00',
            'recurrenceDailyTo' => '14:00',
            'recurrenceWeeklyFrom' => null,
            'recurrenceWeeklyTo' => null,
            'recurrenceMonthlyFrom' => null,
            'recurrenceMonthlyTo' => null,
            'offerDescription' => '1',
        ];

        self::mockPostRewardConfiguration($mockData);
    }

    public static function mockPostRewardConfigurationCase3(?array $freeRoundGameIds = null): void
    {
        $mockData = [
            'id' => 1,
            'name' => 'Bribe',
            'displayName' => 'Display name',
            'type' => RewardConfigurationConstants::TYPE_FREE_ROUNDS,
            'model' => RewardConfigurationConstants::MODEL_DIRECT,
            'status' => RewardConfigurationConstants::STATUS_DISABLED,
            'reason' => RewardConfigurationConstants::REASON_TEST,
            'currency' => Currency::EUR,
            'offeringMethod' => RewardConfigurationConstants::OFFERING_METHOD_MANUAL,
            'offerValidFor' => 2,
            'createdAt' => '2021-11-30 16:38:38',
            'validDuringDays' => 1,
            'segmentIds' => [],
            'claimingEvent' => RewardConfigurationConstants::CLAIMING_EVENT_DIRECT,
            'gameplayRestrictionGameIds' => [5, 6],
            'thumbnail' => 'https://cdn.test-assets.com/wallet/test_logo.jpg',
            'freeRoundConfiguration' => [
                'gameIds' => $freeRoundGameIds ?? [5],
                'roundCount' => null,
                'amount' => 30,
            ],
            'recurrence' => null,
            'offerPeriodFrom' => null,
            'offerPeriodTo' => null,
            'recurrenceDailyFrom' => null,
            'recurrenceDailyTo' => null,
            'recurrenceWeeklyFrom' => null,
            'recurrenceWeeklyTo' => null,
            'recurrenceMonthlyFrom' => null,
            'recurrenceMonthlyTo' => null,
        ];

        self::mockPostRewardConfiguration($mockData);
    }

    public static function mockPatchRewardConfigurationCase2(int $id = 11): void
    {
        $mockData = [
            'id' => $id,
            'name' => 'Bribe',
            'displayName' => 'Display name',
            'type' => RewardConfigurationConstants::TYPE_FREE,
            'model' => RewardConfigurationConstants::MODEL_UPPER,
            'status' => RewardConfigurationConstants::STATUS_ENABLED,
            'reason' => RewardConfigurationConstants::REASON_TEST,
            'currency' => Currency::EUR,
            'offeringMethod' => RewardConfigurationConstants::OFFERING_METHOD_AUTOMATIC,
            'occurrences' => 10,
            'offerAmount' => 39,
            'validDuringDays' => 1,
            'createdAt' => '2021-11-30 16:38:38',
            'segmentIds' => [1, 10],
            'claimingEvent' => RewardConfigurationConstants::CLAIMING_EVENT_DIRECT,
            'gameplayRestrictionGameIds' => [5, 6],
            'thumbnail' => 'https://cdn.test-assets.com/wallet/test_logo.jpg',
            'recurrence' => RewardConfigurationConstants::RECURRENCE_WEEKLY,
            'offerPeriodFrom' => null,
            'offerPeriodTo' => null,
            'recurrenceDailyFrom' => '',
            'recurrenceDailyTo' => '',
            'recurrenceWeeklyFrom' => 'Monday 22:11',
            'recurrenceWeeklyTo' => 'Monday 23:11',
            'recurrenceMonthlyFrom' => null,
            'recurrenceMonthlyTo' => null,
            'offerDescription' => '-',
        ];

        self::mockPatchRewardConfiguration($id, $mockData);
    }

    public static function mockPatchRewardConfigurationCase3(int $id = 11, ?array $freeRoundGameIds = null): void
    {
        $mockData = [
            'id' => 1,
            'domainId' => 1,
            'name' => 'Bribe',
            'displayName' => 'Display name',
            'type' => RewardConfigurationConstants::TYPE_FREE_ROUNDS,
            'model' => RewardConfigurationConstants::MODEL_DIRECT,
            'offeringMethod' => RewardConfigurationConstants::OFFERING_METHOD_AUTOMATIC,
            'offerAmount' => null,
            'wageringMultiplier' => null,
            'status' => RewardConfigurationConstants::STATUS_DISABLED,
            'recurrence' => null,
            'offeringStatus' => RewardConfigurationConstants::OFFERING_STATUS_ACTIVE,
            'offerPeriodFrom' => null,
            'offerPeriodTo' => null,
            'recurrenceDailyFrom' => null,
            'recurrenceDailyTo' => null,
            'recurrenceWeeklyFrom' => null,
            'recurrenceWeeklyTo' => null,
            'recurrenceMonthlyFrom' => '15 22:11',
            'recurrenceMonthlyTo' => '20 23:11',
            'validDuringDays' => 1,
            'occurrences' => null,
            'segmentIds' => [],
            'maxWinMultiplier' => null,
            'offerPercent' => null,
            'offerUpToAmount' => null,
            'createdAt' => '2021-11-30 16:38:38',
            'deletedAt' => null,
            'offerEndAt' => null,
            'freeRoundConfiguration' => [
                'id' => 1,
                'gameIds' => $freeRoundGameIds ?? [5],
                'roundCount' => 4,
                'amount' => 4,
            ],
            'currency' => Currency::EUR,
            'reason' => RewardConfigurationConstants::REASON_TEST,
            'offerDescription' => '- free rounds',
            'claimingEvent' => RewardConfigurationConstants::CLAIMING_EVENT_DIRECT,
            'claimingEventCondition' => null,
            'gameplayRestrictionGameIds' => null,
            'thumbnail' => null,
        ];

        self::mockPatchRewardConfiguration($id, $mockData);
    }

    public static function mockPostRewardConfiguration(array $data): void
    {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . '/api/domain/1/reward-configuration',
            200,
            json_encode($data)
        );
    }

    public static function mockPatchRewardConfiguration(int $id, array $data): void
    {
        self::mockMethod(
            'PATCH',
            self::PROMOTION_HOST . "/api/domain/1/reward-configuration/$id",
            200,
            json_encode($data)
        );
    }

    private static function resolvePromotionConfiguration(string $type, bool $list = false): array
    {
        $configuration = self::$baseSingleMockPromotionConfiguration;
        if ($list) {
            $configuration = self::$baseListMockPromotionConfiguration;
        }

        $configuration['type'] = $type;
        if ($type === PromotionConfigurationConstants::TYPE_REFER_FRIEND) {
            $configuration['options'] = [
                'minimumAmount' => '9.99',
                'targetBetAmount' => '19.99',
                'internalCategoryId' => 11,
            ];
        } else {
            $configuration['rewardingLimit'] = 20;
            $configuration['playerPromotionLimit'] = 5;
            $configuration['schedule'] = self::$basePromotionScheduleMock;
        }

        return $configuration;
    }

    public static function mockGetRewardConfigurationsCount(int $count): void
    {
        self::mockMethod('GET', self::PROMOTION_HOST . '/api/domain/1/reward-configurations/aggregate', 200, json_encode($count));
    }

    public static function mockOfferGift(int $domainId = 1, int $playerId = 1, array $overrides = []): void
    {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/player/$playerId/gift",
            201,
            json_encode(self::promotionGiftRow(1, $playerId, $overrides), JSON_THROW_ON_ERROR)
        );
    }

    public static function mockOfferGiftError(int $domainId, int $playerId, int $code, array $body): void
    {
        self::mockV2Error(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/player/$playerId/gift",
            $code,
            json_encode($body, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockGetGifts(int $domainId = 1, array $gifts = []): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/gifts",
            200,
            json_encode($gifts, JSON_THROW_ON_ERROR)
        );
    }

    /**
     * @param array<int, array<string, mixed>> $configurations
     */
    public static function mockGetPromotionConfigurationsByIds(int $domainId, array $configurations): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/promotion-configurations",
            200,
            json_encode($configurations, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockGetGiftsAggregate(int $domainId, int $count): void
    {
        self::mockMethod('GET', self::PROMOTION_HOST . "/api/domain/$domainId/gifts/aggregate", 200, (string) $count);
    }

    public static function mockGetGiftsError(int $domainId, int $code, array $body): void
    {
        self::mockV2Error(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/gifts",
            $code,
            json_encode($body, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockPostGiftRequest(int $domainId = 1, int $playerId = 1, array $overrides = []): void
    {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/player/$playerId/gift-request",
            201,
            json_encode(self::promotionGiftRequestRow(12, $playerId, $overrides), JSON_THROW_ON_ERROR)
        );
    }

    public static function mockPostGiftRequestError(int $domainId, int $playerId, int $code, array $body): void
    {
        self::mockV2Error(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/player/$playerId/gift-request",
            $code,
            json_encode($body, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockGetDomainGiftRequests(int $domainId = 1, array $requests = []): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/gift-requests",
            200,
            json_encode($requests, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockGetDomainGiftRequestsCount(int $domainId = 1, array $counts = []): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/gift-requests/count",
            200,
            json_encode($counts, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockGetPlayerGiftRequests(int $domainId = 1, int $playerId = 1, array $requests = []): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/player/$playerId/gift-requests",
            200,
            json_encode($requests, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockApproveGiftRequest(int $domainId = 1, int $id = 12, array $overrides = []): void
    {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/gift-request/$id/approve",
            201,
            json_encode(self::promotionGiftRow(5, 1, array_merge([
                'giftRequestId' => $id,
                'requestedByUserId' => 1,
                'requestedAt' => '2026-11-06 10:00:00',
                'approvedByUserId' => 1,
                'approvedAt' => '2026-11-06 11:00:00',
            ], $overrides)), JSON_THROW_ON_ERROR)
        );
    }

    public static function mockApproveGiftRequestError(int $domainId, int $id, int $code, array $body): void
    {
        self::mockV2Error(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/gift-request/$id/approve",
            $code,
            json_encode($body, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockRejectGiftRequest(int $domainId = 1, int $id = 12, array $overrides = []): void
    {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/gift-request/$id/reject",
            200,
            json_encode(self::promotionGiftRequestRow($id, 1, array_merge([
                'status' => 'rejected',
                'rejectedByUserId' => 1,
                'rejectedAt' => '2026-11-06 11:00:00',
                'rejectionReason' => 'Over the monthly budget',
            ], $overrides)), JSON_THROW_ON_ERROR)
        );
    }

    public static function mockRejectGiftRequestError(int $domainId, int $id, int $code, array $body): void
    {
        self::mockV2Error(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/gift-request/$id/reject",
            $code,
            json_encode($body, JSON_THROW_ON_ERROR)
        );
    }

    public static function promotionGiftRequestRow(int $id, int $playerId = 1, array $overrides = []): array
    {
        return array_merge([
            'id' => $id,
            'domainId' => 1,
            'playerId' => $playerId,
            'rewardConfigurationId' => 7,
            'rewardConfigurationName' => 'Birthday hamper',
            'amount' => '150.50',
            'currency' => 'EUR',
            'description' => 'Handed over at the VIP dinner',
            'reasonId' => 4,
            'reasonName' => 'Birthday',
            'status' => 'requested',
            'requestedByUserId' => 1,
            'requestedAt' => '2026-11-06 10:00:00',
            'approvedByUserId' => null,
            'approvedAt' => null,
            'rejectedByUserId' => null,
            'rejectedAt' => null,
            'rejectionReason' => null,
            'createdAt' => '2026-11-06 10:00:00',
            'updatedAt' => '2026-11-06 10:00:00',
        ], $overrides);
    }

    public static function promotionGiftRow(int $id, int $playerId = 1, array $overrides = []): array
    {
        return array_merge([
            'id' => $id,
            'domainId' => 1,
            'playerId' => $playerId,
            'name' => 'Birthday hamper',
            'status' => 'claimed',
            'amount' => '150.50',
            'currency' => 'EUR',
            'rewardConfigurationId' => 7,
            'description' => 'Handed over at the VIP dinner',
            'sourceUserId' => 1,
            'sourceScenarioId' => null,
            'sourcePromotionId' => null,
            'createdAt' => '2026-09-22 10:15:00',
            'updatedAt' => '2026-09-22 10:15:00',
        ], $overrides);
    }

    public static function mockGetRewardOfferingReasons(int $domainId = 1, array $reasons = []): void
    {
        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/reward-offering-reasons",
            200,
            json_encode($reasons, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockGetRewardOfferingReasonsError(int $domainId, int $code, array $body): void
    {
        self::mockV2Error(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/reward-offering-reasons",
            $code,
            json_encode($body, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockPostRewardOfferingReason(int $domainId = 1, array $reason = []): void
    {
        self::mockMethod(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/reward-offering-reason",
            201,
            json_encode($reason, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockPostRewardOfferingReasonError(int $domainId, int $code, array $body): void
    {
        self::mockV2Error(
            'POST',
            self::PROMOTION_HOST . "/api/domain/$domainId/reward-offering-reason",
            $code,
            json_encode($body, JSON_THROW_ON_ERROR)
        );
    }

    public static function mockDeleteRewardOfferingReason(int $domainId = 1, int $id = 1): void
    {
        self::mockMethod(
            'DELETE',
            self::PROMOTION_HOST . "/api/domain/$domainId/reward-offering-reason/$id",
            204,
            null
        );
    }

    public static function mockDeleteRewardOfferingReasonError(int $domainId, int $id, int $code, array $body): void
    {
        self::mockV2Error(
            'DELETE',
            self::PROMOTION_HOST . "/api/domain/$domainId/reward-offering-reason/$id",
            $code,
            json_encode($body, JSON_THROW_ON_ERROR)
        );
    }

    public static function promotionRewardOfferingReasonRow(int $id, array $overrides = []): array
    {
        return array_merge([
            'id' => $id,
            'domainId' => 1,
            'name' => 'Birthday',
            'createdAt' => '2026-10-29 10:00:00',
            'updatedAt' => '2026-10-29 10:00:00',
            'deletedAt' => null,
        ], $overrides);
    }

    public static function mockGetPromotionBonuses(int $count = 1, int $domainId = 1): void
    {
        $data = [];

        for ($id = 1; $id <= $count; ++$id) {
            $data[] = self::promotionBonusRow($id, $domainId);
        }

        self::mockMethod(
            'GET',
            self::PROMOTION_HOST . "/api/domain/$domainId/bonuses",
            200,
            json_encode($data, JSON_THROW_ON_ERROR)
        );
    }

    private static function promotionBonusRow(int $id, int $domainId): array
    {
        return [
            'id' => $id,
            'playerId' => $id,
            'rewardConfiguration' => [
                'id' => $id,
                'domainId' => $domainId,
                'name' => 'Welcome Reward',
                'displayName' => 'Display name',
                'type' => RewardConfigurationConstants::TYPE_DEPOSIT,
                'model' => RewardConfigurationConstants::MODEL_WAGER,
                'offeringMethod' => RewardConfigurationConstants::OFFERING_METHOD_AUTOMATIC,
                'offerAmount' => null,
                'wageringMultiplier' => '6',
                'status' => RewardConfigurationConstants::STATUS_ENABLED,
                'recurrence' => RewardConfigurationConstants::RECURRENCE_UNIQUE,
                'offeringStatus' => RewardConfigurationConstants::OFFERING_STATUS_ACTIVE,
                'offerPeriodFrom' => '2021-12-08 02:06:55',
                'offerPeriodTo' => '2021-12-20 03:22:57',
                'recurrenceDailyFrom' => null,
                'recurrenceDailyTo' => null,
                'recurrenceWeeklyFrom' => null,
                'recurrenceWeeklyTo' => null,
                'recurrenceMonthlyFrom' => null,
                'recurrenceMonthlyTo' => null,
                'validDuringDays' => 1,
                'occurrences' => 1,
                'segmentIds' => [],
                'maxWinMultiplier' => '10',
                'offerPercent' => '100',
                'offerUpToAmount' => '200',
                'createdAt' => '2021-12-08 11:07:20',
                'deletedAt' => null,
                'offerEndAt' => '2021-12-20 03:22:57',
                'freeRoundConfiguration' => [
                    'gameIds' => [],
                    'roundCount' => null,
                    'level' => null,
                ],
                'currency' => Currency::EUR,
                'offerDescription' => '100% up to 200',
                'claimingEvent' => RewardConfigurationConstants::CLAIMING_EVENT_DEPOSIT,
                'claimingEventCondition' => null,
                'gameplayRestrictionGameIds' => null,
            ],
            'wallet' => [
                'id' => $id,
                'uid' => '3e15097a1cda69fb43c91fb3b074f320c0a47cc4bfe5d950ab848336b299d75c',
                'owner_id' => $id,
                'domain_id' => (string) $domainId,
                'last_deposit_at' => '2020-05-29 00:00:00',
                'bonus_offer_allowed' => true,
                'bet_allowed' => true,
                'last_bet_at' => '2020-05-29 00:00:00',
            ],
            'wager' => [
                'wageringAmount' => '50.00',
                'wagerProgressPercent' => '3.00',
            ],
            'amount' => '23.00',
            'amountLimit' => '302.78',
            'currency' => Currency::CAD,
            'status' => BonusConstants::STATUS_CLAIMED,
            'statusSetAt' => null,
            'claimedAt' => '2021-12-08 11:07:20',
            'createdAt' => '2021-12-08 11:07:20',
            'wagerProgressPercent' => '0.00',
            'wagerProgressAmount' => 0,
            'wagerWinAmount' => '138.00',
            'wageringMultiplier' => '6',
            'offeringPeriodTo' => null,
            'validityPeriodTo' => '2021-12-09 11:07:20',
            'model' => RewardConfigurationConstants::MODEL_WAGER,
            'freeRoundsRoundCount' => null,
        ];
    }

    public static function mockGetPromotionBonusesAggregate(int $domainId = 1): void
    {
        self::mockMethod('GET', self::PROMOTION_HOST . "/api/domain/$domainId/bonuses/aggregate", 200, '15');
    }

    public static function mockPatchRewardBonus(int $domainId = 1, int $playerId = 1, int $bonusId = 1): void
    {
        $responseData = [
            'id' => $bonusId,
            'wallet' => [
                'domain_id' => $domainId,
                'id' => 1,
                'uid' => 'c9619f862dd85fce3c3d8731acdfe2616ece2dccd3d550d067611633ddeec486',
                'owner_id' => $playerId,
                'bonus_offer_allowed' => true,
                'bet_allowed' => true,
                'withdrawal_limit' => 200,
                'withdrawal_limit_count' => 200,
                'last_deposit_at' => '2020-05-29 00:00:00',
                'last_bonus_bet_at' => '2020-05-29 00:00:00',
                'last_real_bet_at' => '2020-05-29 00:00:00',
                'last_bet_at' => '2020-05-29 00:00:00',
                'last_bonus_claimed_at' => '2020-05-29 00:00:00',
            ],
            'amount' => 36,
            'currency' => 'CAD',
            'createdAt' => '2022-02-16 10:24:59',
            'updatedAt' => '2022-02-16 10:24:59',
            'totalBalance' => 36,
            'rewardConfiguration' => [
                'id' => 2,
                'domainId' => $domainId,
                'name' => 'Promotional bonus',
                'displayName' => 'Display name',
                'type' => 'free',
                'model' => 'wager',
                'offeringMethod' => 'automatic',
                'offerAmount' => 36,
                'wageringMultiplier' => 2.75,
                'status' => 'enabled',
                'recurrence' => 'unique',
                'offeringStatus' => 'active',
                'offerPeriodFrom' => '2022-02-16 07:55:30',
                'offerPeriodTo' => '2022-03-02 13:06:19',
                'recurrenceDailyFrom' => null,
                'recurrenceDailyTo' => null,
                'recurrenceWeeklyFrom' => null,
                'recurrenceWeeklyTo' => null,
                'recurrenceMonthlyFrom' => null,
                'recurrenceMonthlyTo' => null,
                'offerValidFor' => 14,
                'validDuringDays' => 1,
                'occurrences' => 1,
                'segmentIds' => [],
                'maxWinMultiplier' => 5,
                'offerUpToAmount' => 100,
                'createdAt' => '2020-02-16 07:55:30',
                'deletedAt' => null,
                'offerEndAt' => '2020-02-16 07:55:30',
                'currency' => 'EUR',
                'reason' => null,
                'offerDescription' => '36 &euro;',
                'freeRoundConfiguration' => [],
                'claimingEventCondition' => [],
                'claimingEvent' => 'deposit',
                'gameplayRestrictionGameIds' => [],
                'promotionId' => 1,
                'thumbnail' => 'https://cdn.test-assets.com/wallet/bonus_model/26/thumbnail/logo.png',
            ],
            'amountLimit' => null,
            'status' => 'canceled',
            'claimedAt' => '2021-12-08 11:07:20',
            'freeRoundsRoundCount' => null,
            'wagerProgressPercent' => 0,
            'wagerProgressAmount' => 0,
            'wagerWinAmount' => 108,
            'wageringMultiplier' => 2.75,
            'offeringPeriodTo' => null,
            'validityPeriodTo' => '2021-12-09 11:07:20',
            'model' => 'wager',
            'statusSetAt' => '2022-02-16 10:24:59',
            'gameplayRestrictionGameIds' => [1, 10, 100],
            'promotionId' => 1,
        ];

        self::mockMethod(
            'PATCH',
            self::PROMOTION_HOST . "/api/domain/$domainId/player/$playerId/reward/bonus/$bonusId",
            200,
            json_encode($responseData)
        );
    }

    /**
     * Mock patch reward bonus error response (non-cancelable bonus).
     */
    public static function mockNonCancelableRewardBonus(int $domainId = 1, int $playerId = 1, int $bonusId = 1): void
    {
        self::mockMethod(
            'PATCH',
            self::PROMOTION_HOST . "/api/domain/$domainId/player/$playerId/reward/bonus/$bonusId",
            400,
            '{"errors":["This provider does not allow cancellation of free rounds in progress."]}'
        );
    }
}
