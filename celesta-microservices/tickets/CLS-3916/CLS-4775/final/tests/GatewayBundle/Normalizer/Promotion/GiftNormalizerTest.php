<?php

declare(strict_types=1);

namespace Tests\GatewayBundle\Normalizer\Promotion;

use App\GatewayBundle\Normalizer\Promotion\GiftNormalizer;
use App\Library\PromotionClient;
use App\OAuth2Bundle\Security\User\User;
use App\UserBundle\Entity\User as UserEntity;
use App\UserBundle\Repository\UserRepository;
use CurlLibrary\Exception\V2Exception;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

class GiftNormalizerTest extends TestCase
{
    private const int DOMAIN_ID = 1;

    private UserRepository $userRepository;
    private PromotionClient $promotionClient;
    private LoggerInterface $logger;
    private GiftNormalizer $normalizer;

    protected function setUp(): void
    {
        $this->userRepository = $this->createMock(UserRepository::class);
        $this->promotionClient = $this->createMock(PromotionClient::class);
        $this->logger = $this->createMock(LoggerInterface::class);
        $this->normalizer = new GiftNormalizer($this->userRepository, $this->promotionClient, $this->logger);
    }

    public function testOfferRequestRenamesValueToAmountAndAddsTheSourceUser(): void
    {
        $user = $this->createMock(User::class);
        $user->method('getId')->willReturn(42);

        $result = $this->normalizer->normalizeOfferRequest($user, [
            'rewardConfigurationId' => 7,
            'value' => 150.5,
            'description' => null,
            'reasonId' => 4,
        ]);

        $this->assertSame([
            'rewardConfigurationId' => 7,
            'amount' => '150.5',
            'description' => null,
            'reasonId' => 4,
            'sourceUserId' => 42,
        ], $result);
    }

    public function testOfferRequestSendsANullAmountWhenAbsent(): void
    {
        $user = $this->createMock(User::class);
        $user->method('getId')->willReturn(42);

        $result = $this->normalizer->normalizeOfferRequest($user, ['rewardConfigurationId' => 7, 'value' => null]);

        $this->assertSame(7, $result['rewardConfigurationId']);
        $this->assertNull($result['amount']);
        $this->assertArrayNotHasKey('quantity', $result);
    }

    public function testNormalizeOneReturnsTheConfigurationThePlayerAndTheUpdateTime(): void
    {
        $result = $this->normalizer->normalizeOne(
            self::DOMAIN_ID,
            ['rewardConfigurationId' => 7, 'playerId' => 3, 'updatedAt' => '2026-09-23 08:00:00'] + $this->gift(1, null)
        );

        $this->assertSame(7, $result['rewardConfigurationId']);
        $this->assertSame(3, $result['playerId']);
        $this->assertSame('2026-09-23 08:00:00', $result['updatedAt']);
        $this->assertArrayNotHasKey('quantity', $result);
    }

    public function testNormalizeOneDefaultsTheConfigurationThePlayerAndTheUpdateTimeToNull(): void
    {
        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $this->gift(1, null));

        $this->assertNull($result['rewardConfigurationId']);
        $this->assertNull($result['playerId']);
        $this->assertNull($result['updatedAt']);
    }

    public function testRewardConfigurationRequestFiltersByConfigurationAndDefaultsThePage(): void
    {
        $result = $this->normalizer->normalizeRewardConfigurationRequest([
            'filter' => ['rewardConfigurationIds' => [7]],
            'order' => ['field' => 'createdAt', 'direction' => 'desc'],
        ]);

        $this->assertSame([
            'filter' => ['rewardConfigurationIds' => [7]],
            'limit' => 100,
            'offset' => 0,
            'order' => ['field' => 'createdAt', 'direction' => 'desc'],
        ], $result);
    }

    public function testRewardConfigurationCountRequestKeepsTheAggregateWithoutAPage(): void
    {
        $aggregate = ['aggregator' => 'count', 'field' => 'id'];

        $result = $this->normalizer->normalizeRewardConfigurationRequest([
            'filter' => ['rewardConfigurationIds' => [7]],
            'aggregate' => $aggregate,
        ]);

        $this->assertSame(['filter' => ['rewardConfigurationIds' => [7]], 'aggregate' => $aggregate], $result);
    }

    public function testOfferRequestSendsANullReasonIdWhenAbsent(): void
    {
        $user = $this->createMock(User::class);
        $user->method('getId')->willReturn(42);
        $data = ['name' => 'Watch', 'value' => 300, 'currency' => 'EUR', 'description' => null];

        $this->assertNull($this->normalizer->normalizeOfferRequest($user, $data)['reasonId']);
        $this->assertNull($this->normalizer->normalizeOfferRequest($user, $data + ['reasonId' => null])['reasonId']);
    }

    public function testOfferRequestNeverForwardsTheLegacyReason(): void
    {
        $user = $this->createMock(User::class);
        $user->method('getId')->willReturn(42);

        $result = $this->normalizer->normalizeOfferRequest(
            $user,
            ['name' => 'Watch', 'value' => 300, 'currency' => 'EUR', 'reason' => 'birthday']
        );

        $this->assertArrayNotHasKey('reason', $result);
    }

    public function testNormalizeOneReturnsTheReasonIdAndName(): void
    {
        $gift = ['reasonId' => 4, 'reasonName' => 'Birthday'] + $this->gift(1, null);

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $gift);

        $this->assertSame(4, $result['reasonId']);
        $this->assertSame('Birthday', $result['reason']);
        $this->assertArrayNotHasKey('reasonName', $result);
    }

    public function testListRequestPinsThePlayerAndDefaultsPagination(): void
    {
        $result = $this->normalizer->normalizeRequest(['limit' => null, 'offset' => null, 'order' => ['field' => 'amount', 'direction' => 'desc']], 7);

        $this->assertSame([
            'filter' => ['ownerIds' => [7]],
            'limit' => 100,
            'offset' => 0,
            'order' => ['field' => 'amount', 'direction' => 'desc'],
        ], $result);
    }

    public function testListRequestKeepsExplicitPagination(): void
    {
        $result = $this->normalizer->normalizeRequest(['limit' => 2, 'offset' => 4], 7);

        $this->assertSame(['filter' => ['ownerIds' => [7]], 'limit' => 2, 'offset' => 4], $result);
    }

    public function testNormalizeOneResolvesCreatedBy(): void
    {
        $author = $this->createMock(UserEntity::class);
        $author->method('getId')->willReturn(1);
        $author->method('getFullName')->willReturn('Marta Kulas');
        $this->userRepository->method('getUsersByIds')->with([1])->willReturn([$author]);

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $this->gift(1, 1));

        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result['createdBy']);
        $this->assertNull($result['sourceScenarioId']);
    }

    public function testNormalizeOneCarriesTheScenarioOfAScenarioGift(): void
    {
        $this->userRepository->expects($this->never())->method('getUsersByIds');
        $this->logger->expects($this->never())->method('error');

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $this->gift(1, null, 12));

        $this->assertNull($result['createdBy']);
        $this->assertSame(12, $result['sourceScenarioId']);
    }

    public function testNormalizeOneDefaultsTheScenarioToNullWhenPromotionDoesNotSendIt(): void
    {
        $gift = $this->gift(1, null);
        unset($gift['sourceScenarioId']);

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $gift);

        $this->assertNull($result['sourceScenarioId']);
        $this->assertNull($result['createdBy']);
        $this->assertNull($result['reasonId']);
        $this->assertNull($result['reason']);
    }

    public function testNormalizeManyResolvesCreatedByInOneLookup(): void
    {
        $author = $this->createMock(UserEntity::class);
        $author->method('getId')->willReturn(1);
        $author->method('getFullName')->willReturn('Marta Kulas');
        $this->userRepository->expects($this->once())->method('getUsersByIds')->with([1, 99])->willReturn([$author]);
        $this->logger->expects($this->once())->method('error');

        $result = $this->normalizer->normalizeMany(self::DOMAIN_ID, [
            $this->gift(1, 1),
            $this->gift(2, 1),
            $this->gift(3, 99),
            $this->gift(4, null, 12),
        ]);

        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result[0]['createdBy']);
        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result[1]['createdBy']);
        $this->assertNull($result[2]['createdBy']);
        $this->assertNull($result[3]['createdBy']);
        $this->assertSame(12, $result[3]['sourceScenarioId']);
        $this->assertNull($result[0]['sourceScenarioId']);
        $this->assertSame('150.50', $result[0]['value']);
        $this->assertArrayNotHasKey('amount', $result[0]);
    }

    public function testAGiftWithoutASourceUserHasNoAuthor(): void
    {
        $this->userRepository->expects($this->never())->method('getUsersByIds');
        $this->logger->expects($this->never())->method('error');

        $gift = ['sourceUserId' => null] + $this->gift(1, 1);

        $this->assertNull($this->normalizer->normalizeOne(self::DOMAIN_ID, $gift)['createdBy']);
    }

    public function testNormalizeOneReturnsTheGiftRequestKeysAndResolvesTheirUsers(): void
    {
        $requester = $this->createMock(UserEntity::class);
        $requester->method('getId')->willReturn(2);
        $requester->method('getFullName')->willReturn('Ewa Nowak');
        $approver = $this->createMock(UserEntity::class);
        $approver->method('getId')->willReturn(3);
        $approver->method('getFullName')->willReturn('Jan Kowal');
        $this->userRepository->expects($this->once())->method('getUsersByIds')->with([3, 2])->willReturn([$requester, $approver]);
        $this->logger->expects($this->never())->method('error');

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, [
            'sourceUserId' => 3,
            'giftRequestId' => 12,
            'requestedByUserId' => 2,
            'requestedAt' => '2026-11-06 10:00:00',
            'approvedByUserId' => 3,
            'approvedAt' => '2026-11-06 11:00:00',
        ] + $this->gift(1, 3));

        $this->assertSame(12, $result['giftRequestId']);
        $this->assertSame('2026-11-06 10:00:00', $result['requestedAt']);
        $this->assertSame('2026-11-06 11:00:00', $result['approvedAt']);
        $this->assertSame(['id' => 2, 'name' => 'Ewa Nowak'], $result['requestedBy']);
        $this->assertSame(['id' => 3, 'name' => 'Jan Kowal'], $result['approvedBy']);
    }

    public function testNormalizeOneReturnsNullGiftRequestKeysWhenPromotionOmitsThem(): void
    {
        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $this->gift(1, null));

        $this->assertNull($result['giftRequestId']);
        $this->assertNull($result['requestedAt']);
        $this->assertNull($result['approvedAt']);
        $this->assertNull($result['requestedBy']);
        $this->assertNull($result['approvedBy']);
    }

    public function testAnUnresolvedRequesterGivesANullNameAndAnErrorLog(): void
    {
        $this->userRepository->method('getUsersByIds')->willReturn([]);
        $this->logger->expects($this->once())->method('error');

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, ['requestedByUserId' => 99] + $this->gift(1, null));

        $this->assertNull($result['requestedBy']);
    }

    public function testAPromotionGiftResolvesToItsPromotionConfiguration(): void
    {
        $this->userRepository->expects($this->never())->method('getUsersByIds');
        $this->logger->expects($this->never())->method('error');
        $this->promotionClient->expects($this->once())
            ->method('getPromotionConfigurations')
            ->with(self::DOMAIN_ID, ['filter' => ['ids' => [5]], 'limit' => 1, 'offset' => 0])
            ->willReturn([$this->configuration(5, 'VIP tier')]);

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $this->promotionGift(1, 5));

        $this->assertSame(['id' => 5, 'name' => 'VIP tier'], $result['createdBy']);
        $this->assertSame(5, $result['sourcePromotionId']);
        $this->assertNull($result['sourceScenarioId']);
    }

    public function testNormalizeManyLooksUpTheUsersAndThePromotionsOncePerList(): void
    {
        $author = $this->createMock(UserEntity::class);
        $author->method('getId')->willReturn(1);
        $author->method('getFullName')->willReturn('Marta Kulas');
        $this->userRepository->expects($this->once())->method('getUsersByIds')->with([1])->willReturn([$author]);
        $this->promotionClient->expects($this->once())
            ->method('getPromotionConfigurations')
            ->with(self::DOMAIN_ID, ['filter' => ['ids' => [5, 6]], 'limit' => 2, 'offset' => 0])
            ->willReturn([$this->configuration(6, 'Birthday'), $this->configuration(5, 'VIP tier')]);
        $this->logger->expects($this->never())->method('error');

        $result = $this->normalizer->normalizeMany(self::DOMAIN_ID, [
            $this->gift(1, 1),
            $this->promotionGift(2, 5),
            $this->gift(3, null, 12),
            $this->promotionGift(4, 6),
            $this->promotionGift(5, 5),
        ]);

        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result[0]['createdBy']);
        $this->assertNull($result[0]['sourcePromotionId']);
        $this->assertSame(['id' => 5, 'name' => 'VIP tier'], $result[1]['createdBy']);
        $this->assertSame(5, $result[1]['sourcePromotionId']);
        $this->assertNull($result[2]['createdBy']);
        $this->assertSame(12, $result[2]['sourceScenarioId']);
        $this->assertNull($result[2]['sourcePromotionId']);
        $this->assertSame(['id' => 6, 'name' => 'Birthday'], $result[3]['createdBy']);
        $this->assertSame(['id' => 5, 'name' => 'VIP tier'], $result[4]['createdBy']);
    }

    public function testNoPromotionIsLookedUpWhenNoGiftHasASourcePromotion(): void
    {
        $this->promotionClient->expects($this->never())->method('getPromotionConfigurations');

        $result = $this->normalizer->normalizeMany(self::DOMAIN_ID, [$this->gift(1, null), $this->gift(2, null, 12)]);

        $this->assertNull($result[0]['sourcePromotionId']);
        $this->assertNull($result[1]['sourcePromotionId']);
    }

    public function testAPromotionMissingFromTheLookupGivesANullCreatedByAndLogsIt(): void
    {
        $this->promotionClient->method('getPromotionConfigurations')->willReturn([$this->configuration(6, 'Birthday')]);
        $this->logger->expects($this->once())
            ->method('error')
            ->with(
                'Gift source promotion does not resolve to a promotion configuration',
                ['gift_id' => 1, 'source_promotion_id' => 5],
            );

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $this->promotionGift(1, 5));

        $this->assertNull($result['createdBy']);
        $this->assertSame(5, $result['sourcePromotionId']);
    }

    public function testAFailedPromotionLookupGivesANullCreatedByToPromotionGiftsOnly(): void
    {
        $author = $this->createMock(UserEntity::class);
        $author->method('getId')->willReturn(1);
        $author->method('getFullName')->willReturn('Marta Kulas');
        $this->userRepository->method('getUsersByIds')->willReturn([$author]);
        $this->promotionClient->expects($this->once())
            ->method('getPromotionConfigurations')
            ->willThrowException(new V2Exception('promotion is down'));
        $this->logger->expects($this->once())
            ->method('error')
            ->with('Gift source promotions could not be fetched', ['source_promotion_ids' => [5, 6]]);

        $result = $this->normalizer->normalizeMany(self::DOMAIN_ID, [
            $this->gift(1, 1),
            $this->promotionGift(2, 5),
            $this->promotionGift(3, 6),
        ]);

        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result[0]['createdBy']);
        $this->assertNull($result[1]['createdBy']);
        $this->assertNull($result[2]['createdBy']);
        $this->assertSame(5, $result[1]['sourcePromotionId']);
    }

    public function testNormalizeOneDefaultsTheSourcePromotionToNullWhenPromotionDoesNotSendIt(): void
    {
        $this->promotionClient->expects($this->never())->method('getPromotionConfigurations');
        $gift = $this->gift(1, null);
        unset($gift['sourcePromotionId']);

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, $gift);

        $this->assertNull($result['sourcePromotionId']);
        $this->assertNull($result['createdBy']);
    }

    public function testASourceUserWinsOverASourcePromotion(): void
    {
        $author = $this->createMock(UserEntity::class);
        $author->method('getId')->willReturn(1);
        $author->method('getFullName')->willReturn('Marta Kulas');
        $this->userRepository->method('getUsersByIds')->willReturn([$author]);
        $this->promotionClient->method('getPromotionConfigurations')->willReturn([$this->configuration(5, 'VIP tier')]);

        $result = $this->normalizer->normalizeOne(self::DOMAIN_ID, ['sourcePromotionId' => 5] + $this->gift(1, 1));

        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result['createdBy']);
    }

    public function testPromotionAmountErrorsAreRenamedToValueInTheFormChildren(): void
    {
        $result = $this->normalizer->mapPromotionErrors([
            'message' => 'Validation Failed',
            'children' => [
                'amount' => ['errors' => ['too many decimals']],
                'currency' => ['errors' => ['not held']],
            ],
        ]);

        $this->assertSame([
            'value' => ['errors' => ['too many decimals']],
            'currency' => ['errors' => ['not held']],
        ], $result['children']);
    }

    public function testPromotionAmountErrorsAreRenamedToValueInTheBareFieldMap(): void
    {
        $result = $this->normalizer->mapPromotionErrors(['amount' => ['too many decimals'], 'currency' => ['not held']]);

        $this->assertSame(['value' => ['too many decimals'], 'currency' => ['not held']], $result);
    }

    public function testPromotionErrorsWithoutAmountAreLeftUntouched(): void
    {
        $errors = ['message' => 'Validation Failed', 'errors' => ['currency' => ['not held']]];

        $this->assertSame($errors, $this->normalizer->mapPromotionErrors($errors));
    }

    public function testPromotionReasonErrorsAreLeftUntouchedByTheValueRename(): void
    {
        $result = $this->normalizer->mapPromotionErrors([
            'message' => 'Validation Failed',
            'errors' => ['amount' => ['too many decimals'], 'reason' => ['too long']],
        ]);

        $this->assertSame(['value' => ['too many decimals'], 'reason' => ['too long']], $result['errors']);
    }

    public function testPromotionAmountErrorsAreRenamedToValue(): void
    {
        $result = $this->normalizer->mapPromotionErrors([
            'message' => 'Validation Failed',
            'errors' => ['amount' => ['too many decimals'], 'currency' => ['not held']],
        ]);

        $this->assertSame(['value' => ['too many decimals'], 'currency' => ['not held']], $result['errors']);
    }

    private function promotionGift(int $id, int $sourcePromotionId): array
    {
        return ['sourcePromotionId' => $sourcePromotionId] + $this->gift($id, null);
    }

    private function configuration(int $id, string $name): array
    {
        return ['id' => $id, 'name' => $name, 'status' => 'enabled'];
    }

    private function gift(int $id, ?int $sourceUserId, ?int $sourceScenarioId = null): array
    {
        return [
            'id' => $id,
            'status' => 'claimed',
            'name' => 'Gift',
            'amount' => '150.50',
            'currency' => 'EUR',
            'description' => null,
            'sourceUserId' => $sourceUserId,
            'sourceScenarioId' => $sourceScenarioId,
            'sourcePromotionId' => null,
            'createdAt' => '2026-09-22 10:15:00',
        ];
    }
}
