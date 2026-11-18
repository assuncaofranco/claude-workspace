<?php

namespace Tests\GatewayBundle\Controller\Promotion;

use Symfony\Component\HttpFoundation\Response;
use Tests\GatewayBundle\GatewayTestCase;
use Tests\Support\QueryAwareMockClient;

class GiftControllerHttpTest extends GatewayTestCase
{
    use GiftControllerTestTrait;

    public function testPostGiftUnauthorized(): void
    {
        $this->checkUnauthorized('POST', self::OFFER_URL);
    }

    public function testForbiddenWithoutOfferGiftPermission(): void
    {
        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => self::$restrictedAccessToken]);

        $this->assertSame(Response::HTTP_FORBIDDEN, self::$client->getResponse()->getStatusCode());
    }

    public function testRecordsAGiftAndReturnsItNormalized(): void
    {
        self::mockGetPlayer();
        self::mockOfferGift(1, 1, ['reasonId' => 4, 'reasonName' => 'Birthday']);

        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $this->assertSame([
            'id' => 1,
            'playerId' => 1,
            'status' => 'claimed',
            'name' => 'Birthday hamper',
            'value' => '150.50',
            'currency' => 'EUR',
            'rewardConfigurationId' => 7,
            'description' => 'Handed over at the VIP dinner',
            'reasonId' => 4,
            'reason' => 'Birthday',
            'createdBy' => ['id' => 1, 'name' => 'Marta Kulas'],
            'sourceScenarioId' => null,
            'sourcePromotionId' => null,
            'createdAt' => '2026-09-22 10:15:00',
            'updatedAt' => '2026-09-22 10:15:00',
            'giftRequestId' => null,
            'requestedAt' => null,
            'approvedAt' => null,
            'requestedBy' => null,
            'approvedBy' => null,
        ], json_decode($response->getContent(), true));
        $forwarded = json_decode(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH), true);
        $this->assertSame(4, $forwarded['reasonId']);
        $this->assertSame(7, $forwarded['rewardConfigurationId']);
        $this->assertSame('150.5', $forwarded['amount']);
        $this->assertArrayNotHasKey('quantity', $forwarded);
        $this->assertArrayNotHasKey('name', $forwarded);
        $this->assertArrayNotHasKey('currency', $forwarded);
        $this->assertArrayNotHasKey('reason', $forwarded);
    }

    public function testGetGiftsUnauthorized(): void
    {
        $this->checkUnauthorized('GET', self::LIST_URL);
    }

    public function testForbiddenWithoutAccessGiftTabPermission(): void
    {
        self::$client->request('GET', self::LIST_URL, [], [], ['HTTP_Authorization' => self::$restrictedAccessToken]);

        $this->assertSame(Response::HTTP_FORBIDDEN, self::$client->getResponse()->getStatusCode());
    }
}
