<?php

namespace Tests\GatewayBundle\Normalizer\Player;

use App\GatewayBundle\Normalizer\Player\LogNormalizer;
use JobLibrary\Job\Activity\UserActivityJob;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Translation\Loader\ArrayLoader;
use Symfony\Component\Translation\Translator;

class LogNormalizerDescriptionTest extends TestCase
{
    private const array MESSAGES = [
        'player.list.status.active' => 'Active',
        'player.list.status.locked' => 'Locked',
        'player.list.kyc_status.not_verified' => 'Not verified',
        'player.list.kyc_status.verified' => 'Verified',
        'player.logs.table.segment_logs' => 'segment id: segmentId',
        'player.logs.table.event.logout' => 'N/A',
        'player.logs.table.event.session_expired' => 'Inactivity',
        'player.logs.table.event.stl_reached' => 'The player has been logged out for STL reached.',
        'player.logs.description.multiple_accounts' => 'Multiple Accounts',
        'player.logs.description.gift_offered' => '%name% | %value% %currency%',
        'player.logs.description.gift_offered_reason' => 'Reason: %reason%',
        'player.logs.description.gift_requested' => '%name% | %value% %currency%',
        'player.logs.description.gift_request_rejected' => '%name% | %value% %currency%',
        'player.logs.description.gift_request_rejected_reason' => 'Rejection reason: %reason%',
    ];

    /**
     * @param array<string, bool|int|string> $additionalData
     */
    #[DataProvider('descriptionProvider')]
    public function testNormalizeDescribesTheEvent(
        string $event,
        string $sourceType,
        array $additionalData,
        string $expected,
    ): void {
        $output = $this->normalizer()->normalize([
            'event' => $event,
            'domain_id' => 1,
            'source_type' => $sourceType,
            'source_user_id' => 1,
            'created_at' => '2024-05-02 10:00:00',
            'additional_data' => $additionalData,
        ]);

        $this->assertSame($expected, $output['description']);
    }

    /**
     * @return iterable<string, array{string, string, array<string, bool|int|string>, string}>
     */
    public static function descriptionProvider(): iterable
    {
        $user = UserActivityJob::SOURCE_TYPE_USER;
        $system = UserActivityJob::SOURCE_TYPE_SYSTEM;

        yield 'status changed' => [
            UserActivityJob::EVENT_PLAYER_STATUS_CHANGED,
            $user,
            ['last_status' => 'active', 'new_status' => 'locked'],
            'Active -> Locked',
        ];
        yield 'gift offered with a reason' => [
            UserActivityJob::EVENT_GIFT_OFFERED,
            $user,
            ['name' => 'Birthday hamper', 'value' => '150.50', 'currency' => 'EUR', 'reason_name' => 'Birthday'],
            'Birthday hamper | 150.50 EUR | Reason: Birthday',
        ];
        yield 'gift offered without a reason' => [
            UserActivityJob::EVENT_GIFT_OFFERED,
            $user,
            ['name' => 'Birthday hamper', 'value' => '150.50', 'currency' => 'EUR', 'reason_name' => null],
            'Birthday hamper | 150.50 EUR',
        ];
        yield 'gift requested with a reason' => [
            UserActivityJob::EVENT_GIFT_REQUESTED,
            $user,
            ['name' => 'Birthday hamper', 'value' => '150.50', 'currency' => 'EUR', 'reason_name' => 'Birthday'],
            'Birthday hamper | 150.50 EUR | Reason: Birthday',
        ];
        yield 'gift requested without a reason' => [
            UserActivityJob::EVENT_GIFT_REQUESTED,
            $user,
            ['name' => 'Birthday hamper', 'value' => '150.50', 'currency' => 'EUR'],
            'Birthday hamper | 150.50 EUR',
        ];
        yield 'gift request rejected with a reason and a rejection reason' => [
            UserActivityJob::EVENT_GIFT_REQUEST_REJECTED,
            $user,
            ['name' => 'Birthday hamper', 'value' => '150.50', 'currency' => 'EUR', 'reason_name' => 'Birthday', 'rejection_reason' => 'Over the budget'],
            'Birthday hamper | 150.50 EUR | Reason: Birthday | Rejection reason: Over the budget',
        ];
        yield 'gift request rejected without data' => [UserActivityJob::EVENT_GIFT_REQUEST_REJECTED, $user, [], ' |  '];
        yield 'promotion gift offered with a reason' => [
            UserActivityJob::EVENT_GIFT_OFFERED,
            UserActivityJob::SOURCE_TYPE_PROMOTION,
            ['name' => 'Birthday hamper', 'value' => '150.50', 'currency' => 'EUR', 'reason_name' => 'Birthday'],
            'Birthday hamper | 150.50 EUR | Reason: Birthday',
        ];
        yield 'promotion gift offered without a reason' => [
            UserActivityJob::EVENT_GIFT_OFFERED,
            UserActivityJob::SOURCE_TYPE_PROMOTION,
            ['name' => 'Birthday hamper', 'value' => '150.50', 'currency' => 'EUR', 'reason_name' => null],
            'Birthday hamper | 150.50 EUR',
        ];
        yield 'gift offered without data' => [UserActivityJob::EVENT_GIFT_OFFERED, $user, [], ' |  '];
        yield 'status changed without statuses' => [UserActivityJob::EVENT_PLAYER_STATUS_CHANGED, $user, [], ' -> '];
        yield 'status changed with a reason' => [
            UserActivityJob::EVENT_PLAYER_STATUS_CHANGED,
            $user,
            ['last_status' => 'active', 'new_status' => 'locked', 'reason' => 'multiple_accounts'],
            'Active -> Locked | Multiple Accounts',
        ];
        yield 'status changed with a null reason' => [
            UserActivityJob::EVENT_PLAYER_STATUS_CHANGED,
            $user,
            ['last_status' => 'active', 'new_status' => 'locked', 'reason' => 'null'],
            'Active -> Locked',
        ];
        yield 'affiliate changed' => [
            UserActivityJob::EVENT_PLAYER_AFFILIATE_ID_CHANGED,
            $user,
            ['affiliate_id_before' => 3, 'affiliate_id_after' => 5],
            '3 -> 5',
        ];
        yield 'segment assigned' => [
            UserActivityJob::EVENT_SEGMENT_ASSIGNED,
            $system,
            ['segment_id' => 7],
            'segment id: 7',
        ];
        yield 'segment unassigned' => [
            UserActivityJob::EVENT_SEGMENT_UNASSIGNED,
            $system,
            ['segment_id' => 7],
            'segment id: 7',
        ];
        yield 'logout' => [UserActivityJob::EVENT_LOGOUT, UserActivityJob::SOURCE_TYPE_PLAYER, [], 'N/A'];
        yield 'session expired' => [UserActivityJob::EVENT_SESSION_EXPIRED, $system, [], 'Inactivity'];
        yield 'session time limit reached' => [
            UserActivityJob::EVENT_STL_REACHED,
            $system,
            [],
            'The player has been logged out for STL reached.',
        ];
        yield 'kyc status changed' => [
            UserActivityJob::EVENT_KYC_STATUS_CHANGED,
            $user,
            ['last_kyc_status' => 'not_verified', 'new_kyc_status' => 'verified'],
            'Not verified -> Verified',
        ];
        yield 'kyc status changed without statuses' => [UserActivityJob::EVENT_KYC_STATUS_CHANGED, $user, [], ' -> '];
        yield 'score updated' => [
            UserActivityJob::EVENT_PLAYER_SCORE_UPDATED,
            $system,
            ['type' => 'rg', 'from_value' => 'low', 'to_value' => 'high'],
            'rg score: low -> high',
        ];
        yield 'responsible gaming limit changed' => [
            UserActivityJob::EVENT_RG_LIMIT_CHANGED,
            $user,
            ['period' => 'day', 'type' => 'deposit', 'from_value' => 100, 'to_value' => 50],
            'day deposit: 100 -> 50',
        ];
        yield 'offer bonus updated by a user' => [
            UserActivityJob::EVENT_OFFER_BONUS_UPDATED,
            $user,
            ['from_value' => true, 'to_value' => false],
            'true -> false',
        ];
        yield 'bet allowed updated by a user' => [
            UserActivityJob::EVENT_BET_ALLOWED_UPDATED,
            $user,
            ['from_value' => false, 'to_value' => true],
            'false -> true',
        ];
        yield 'deposit allowed updated by the system' => [
            UserActivityJob::EVENT_DEPOSIT_ALLOWED_UPDATED,
            $system,
            ['from_value' => true, 'to_value' => false, 'rule_result_id' => 12],
            'true -> false | Fraud alert ID: 12',
        ];
        yield 'sanctions updated by a user' => [
            UserActivityJob::EVENT_SANCTIONS_UPDATED,
            $user,
            ['from_value' => 'no_hit', 'to_value' => 'hit'],
            'no_hit -> hit',
        ];
        yield 'auto withdrawal threshold changed by the system' => [
            UserActivityJob::EVENT_AUTO_WITHDRAWAL_THRESHOLD_CHANGED,
            $system,
            ['from_value' => 100, 'to_value' => 200, 'rule_result_id' => 3],
            '100 -> 200 | Fraud alert ID: 3',
        ];
    }

    private function normalizer(): LogNormalizer
    {
        $translator = new Translator('en');
        $translator->addLoader('array', new ArrayLoader());
        $translator->addResource('array', self::MESSAGES, 'en');

        return new LogNormalizer($translator);
    }
}
