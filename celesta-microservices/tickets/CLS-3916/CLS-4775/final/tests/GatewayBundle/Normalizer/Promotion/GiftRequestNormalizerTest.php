<?php

declare(strict_types=1);

namespace Tests\GatewayBundle\Normalizer\Promotion;

use App\GatewayBundle\Normalizer\Promotion\GiftNormalizer;
use App\GatewayBundle\Normalizer\Promotion\GiftRequestNormalizer;
use App\Library\PromotionClient;
use App\OAuth2Bundle\Security\User\User;
use App\UserBundle\Entity\User as UserEntity;
use App\UserBundle\Repository\UserRepository;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;
use Tests\Traits\PromotionClientMockTrait;

class GiftRequestNormalizerTest extends TestCase
{
    use PromotionClientMockTrait;

    private UserRepository $userRepository;
    private LoggerInterface $logger;
    private GiftRequestNormalizer $normalizer;
    private User $user;

    protected function setUp(): void
    {
        $this->userRepository = $this->createMock(UserRepository::class);
        $this->logger = $this->createMock(LoggerInterface::class);
        $this->normalizer = new GiftRequestNormalizer(
            new GiftNormalizer($this->userRepository, $this->createMock(PromotionClient::class), $this->logger),
        );
        $this->user = $this->createMock(User::class);
        $this->user->method('getId')->willReturn(42);
    }

    public function testCreateRequestRenamesValueToAmountAndAddsTheRequestingUser(): void
    {
        $result = $this->normalizer->normalizeCreateRequest($this->user, [
            'rewardConfigurationId' => 7,
            'value' => 150.5,
            'description' => 'VIP dinner',
            'reasonId' => 4,
        ]);

        $this->assertSame([
            'rewardConfigurationId' => 7,
            'amount' => '150.5',
            'description' => 'VIP dinner',
            'reasonId' => 4,
            'requestedByUserId' => 42,
        ], $result);
    }

    public function testCreateRequestSendsNullsWhenTheOptionalFieldsAreAbsent(): void
    {
        $result = $this->normalizer->normalizeCreateRequest($this->user, ['rewardConfigurationId' => 7, 'value' => null]);

        $this->assertNull($result['amount']);
        $this->assertNull($result['description']);
        $this->assertNull($result['reasonId']);
    }

    public function testApproveRequestCarriesTheApprover(): void
    {
        $this->assertSame(['approvedByUserId' => 42], $this->normalizer->normalizeApproveRequest($this->user));
    }

    public function testRejectRequestCarriesTheRejecterAndTheReason(): void
    {
        $this->assertSame(
            ['rejectedByUserId' => 42, 'rejectionReason' => 'Over the budget'],
            $this->normalizer->normalizeRejectRequest($this->user, ['rejectionReason' => 'Over the budget'])
        );
    }

    public function testRequestsWithoutAReasonCarryNone(): void
    {
        $this->assertSame(['rejectedByUserId' => 42], $this->normalizer->normalizeRejectRequest($this->user, ['rejectionReason' => '']));
        $this->assertSame(
            ['approvedByUserId' => 42, 'reason' => 'Within budget'],
            $this->normalizer->normalizeApproveRequest($this->user, ['reason' => 'Within budget'])
        );
    }

    public function testListQueryForwardsTheFilterWithoutEmptyKeys(): void
    {
        $this->assertSame(
            ['limit' => 2, 'offset' => 4, 'filter' => ['playerIds' => [7], 'statuses' => ['approved']]],
            $this->normalizer->normalizeListQuery([
                'limit' => 2,
                'offset' => 4,
                'filter' => ['ids' => [], 'playerIds' => [7], 'currencies' => [], 'statuses' => ['approved']],
            ])
        );
    }

    public function testListQueryDefaultsThePaginationAndKeepsTheOrder(): void
    {
        $this->assertSame(
            ['limit' => 100, 'offset' => 0, 'order' => ['field' => 'amount', 'direction' => 'desc']],
            $this->normalizer->normalizeListQuery(['limit' => null, 'offset' => null, 'order' => ['field' => 'amount', 'direction' => 'desc']])
        );
        $this->assertSame(['limit' => 2, 'offset' => 4], $this->normalizer->normalizeListQuery(['limit' => 2, 'offset' => 4]));
    }

    public function testNormalizeOneRenamesAmountToValueAndResolvesTheUsers(): void
    {
        $requester = $this->createMock(UserEntity::class);
        $requester->method('getId')->willReturn(1);
        $requester->method('getFullName')->willReturn('Marta Kulas');
        $this->userRepository->expects($this->once())->method('getUsersByIds')->with([1])->willReturn([$requester]);
        $this->logger->expects($this->never())->method('error');

        $result = $this->normalizer->normalizeOne(self::promotionGiftRequestRow(12));

        $this->assertSame('150.50', $result['value']);
        $this->assertArrayNotHasKey('amount', $result);
        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result['requestedBy']);
        $this->assertNull($result['approvedBy']);
        $this->assertNull($result['rejectedBy']);
        $this->assertSame(12, $result['id']);
        $this->assertSame('requested', $result['status']);
    }

    public function testNormalizeManyResolvesAllUsersInOneLookupAndLogsAnUnresolvedOne(): void
    {
        $requester = $this->createMock(UserEntity::class);
        $requester->method('getId')->willReturn(1);
        $requester->method('getFullName')->willReturn('Marta Kulas');
        $this->userRepository->expects($this->once())->method('getUsersByIds')->with([1, 99])->willReturn([$requester]);
        $this->logger->expects($this->once())->method('error');

        $result = $this->normalizer->normalizeMany([
            self::promotionGiftRequestRow(12),
            self::promotionGiftRequestRow(13, 1, ['status' => 'rejected', 'rejectedByUserId' => 99]),
        ]);

        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result[0]['requestedBy']);
        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $result[1]['requestedBy']);
        $this->assertNull($result[1]['rejectedBy']);
    }

    public function testNormalizeManyOfNothingDoesNotLookUpUsers(): void
    {
        $this->userRepository->expects($this->never())->method('getUsersByIds');

        $this->assertSame([], $this->normalizer->normalizeMany([]));
    }
}
