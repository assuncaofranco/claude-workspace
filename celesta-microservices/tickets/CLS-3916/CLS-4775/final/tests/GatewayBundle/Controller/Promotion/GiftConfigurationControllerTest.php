<?php

namespace Tests\GatewayBundle\Controller\Promotion;

use Generator;
use Lancaster\Constants\Currency\Currency;
use PHPUnit\Framework\Attributes\DataProvider;
use Symfony\Component\HttpFoundation\Response;
use Tests\GatewayBundle\ControllerTestCase;
use Tests\Support\QueryAwareMockClient;

class GiftConfigurationControllerTest extends ControllerTestCase
{
    use GiftConfigurationControllerTestTrait;

    private const string PROMOTION_EDIT_PATH = 'api/domain/1/reward-configuration/5';

    private const string PROMOTION_GIFTS_PATH = 'api/domain/1/gifts';

    private const string PROMOTION_GIFTS_AGGREGATE_PATH = 'api/domain/1/gifts/aggregate';

    private const string CURRENCY_NOT_ENABLED = 'This currency is not enabled for the brand.';

    public function testCreateForwardsTheStockAndReturnsItWithTheOfferedCount(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();
        self::mockPostRewardConfiguration(self::giftConfigurationData(['stock' => 50, 'offeredCount' => 0]));

        $response = $this->request('POST', self::CREATE_URL, [
            'name' => 'Bottle of wine',
            'currency' => 'EUR',
            'offerAmount' => 25.5,
            'stock' => 50,
        ]);

        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $this->assertSame(50, $content['stock']);
        $this->assertSame(0, $content['offeredCount']);
        $forwarded = json_decode(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_CREATE_PATH), true);
        $this->assertSame(50, $forwarded['stock']);
    }

    /**
     * @param array<string, scalar|null> $override
     */
    #[DataProvider('invalidBodyProvider')]
    public function testCreateRejectsAnInvalidBodyBeforeCallingPromotion(array $override, string $field): void
    {
        QueryAwareMockClient::resetLastRequestBodies();

        $response = $this->request('POST', self::CREATE_URL, array_merge([
            'name' => 'Bottle of wine',
            'currency' => 'EUR',
            'offerAmount' => 25.5,
        ], $override));

        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertNotEmpty($content['errors']['children'][$field]['errors']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_CREATE_PATH));
    }

    public static function invalidBodyProvider(): Generator
    {
        yield 'blank name' => [['name' => ''], 'name'];
        yield 'zero value' => [['offerAmount' => 0], 'offerAmount'];
        yield 'three decimals' => [['offerAmount' => '1.234'], 'offerAmount'];
        yield 'unknown currency' => [['currency' => 'XXX'], 'currency'];
        yield 'missing value' => [['offerAmount' => null], 'offerAmount'];
        yield 'zero stock' => [['stock' => 0], 'stock'];
        yield 'decimal stock' => [['stock' => '1.5'], 'stock'];
    }

    #[DataProvider('currencyProvider')]
    public function testCreateForwardsTheStoredCodeOfTheCurrency(string $submitted, string $expected): void
    {
        QueryAwareMockClient::resetLastRequestBodies();
        self::mockPostRewardConfiguration(self::giftConfigurationData(['currency' => $expected]));

        $response = $this->request('POST', self::CREATE_URL, [
            'name' => 'Bottle of wine',
            'currency' => $submitted,
            'offerAmount' => 25.5,
        ]);

        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $forwarded = json_decode(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_CREATE_PATH), true);
        $this->assertSame($expected, $forwarded['currency']);
    }

    #[DataProvider('currencyNotEnabledForTheBrandProvider')]
    public function testCreateRejectsACurrencyNotEnabledForTheBrandBeforeCallingPromotion(string $currency): void
    {
        QueryAwareMockClient::resetLastRequestBodies();

        $response = $this->request('POST', self::CREATE_URL, [
            'name' => 'Bottle of wine',
            'currency' => $currency,
            'offerAmount' => 25.5,
        ]);

        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame([self::CURRENCY_NOT_ENABLED], $content['errors']['children']['currency']['errors']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_CREATE_PATH));
    }

    public function testEditRejectsACurrencyNotEnabledForTheBrandBeforeCallingPromotion(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();

        $response = $this->request('PUT', self::EDIT_URL, [
            'name' => 'Bottle of wine',
            'currency' => Currency::GBP,
            'offerAmount' => 25.5,
        ]);

        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame([self::CURRENCY_NOT_ENABLED], $content['errors']['children']['currency']['errors']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('patch', self::PROMOTION_EDIT_PATH));
    }

    public static function currencyNotEnabledForTheBrandProvider(): Generator
    {
        yield 'disabled for the brand' => [Currency::GBP];
        yield 'not offered by the brand' => [Currency::JPY];
    }

    public static function currencyProvider(): Generator
    {
        yield 'four char code is converted' => ['USDT', 'UST'];
        yield 'stored code is kept' => ['UST', 'UST'];
        yield 'fiat is kept' => ['EUR', 'EUR'];
    }

    public function testCreateMapsAPromotionValidationErrorOntoTheForm(): void
    {
        self::mockV2Error('POST', self::PROMOTION_HOST . '/' . self::PROMOTION_CREATE_PATH, Response::HTTP_BAD_REQUEST, json_encode([
            'message' => 'Validation Failed',
            'errors' => ['name' => ['This value is too long.']],
        ], JSON_THROW_ON_ERROR));

        $response = $this->request('POST', self::CREATE_URL, [
            'name' => 'Bottle of wine',
            'currency' => 'EUR',
            'offerAmount' => 25.5,
        ]);

        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['errors' => ['This value is too long.']], $content['errors']['children']['name']);
    }

    public function testEditReturnsAPromotionServerError(): void
    {
        self::mockV2Error('PATCH', self::PROMOTION_HOST . '/' . self::PROMOTION_EDIT_PATH);

        $response = $this->request('PUT', self::EDIT_URL, [
            'name' => 'Magnum',
            'currency' => 'EUR',
            'offerAmount' => 25.5,
        ]);

        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['Internal Server Error', 'code' => 'VALIDATION_CONSTRAINT'], json_decode($response->getContent(), true));
    }

    public function testEditSendsNoTypeAndClearsTheOptionalFields(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();
        self::mockPatchRewardConfiguration(5, self::giftConfigurationData(['id' => 5, 'name' => 'Magnum']));

        $response = $this->request('PUT', self::EDIT_URL, [
            'name' => 'Magnum',
            'currency' => 'EUR',
            'offerAmount' => 25.5,
        ]);

        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $this->assertSame('Magnum', json_decode($response->getContent(), true)['name']);
        $this->assertEquals([
            'name' => 'Magnum',
            'currency' => 'EUR',
            'offerAmount' => '25.5',
            'displayName' => null,
            'reason' => null,
            'stock' => null,
        ], json_decode(QueryAwareMockClient::getLastRequestBody('patch', self::PROMOTION_EDIT_PATH), true));
    }

    public function testEditRejectsAnInvalidBodyBeforeCallingPromotion(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();

        $response = $this->request('PUT', self::EDIT_URL, ['name' => '', 'currency' => 'EUR', 'offerAmount' => 25.5]);

        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('patch', self::PROMOTION_EDIT_PATH));
    }

    public function testListsTheGiftsOfAConfigurationWithTheirPlayers(): void
    {
        QueryAwareMockClient::resetLastRequestQueries();
        self::mockGetGifts(1, [self::promotionGiftRow(4, 12, ['reasonId' => 2, 'reasonName' => 'Birthday'])]);

        self::$client->request(
            'GET',
            self::GIFTS_URL,
            [
                'filter' => ['rewardConfigurationIds' => ['7']],
                'limit' => 10,
                'offset' => 20,
                'order' => ['field' => 'createdAt', 'direction' => 'desc'],
            ],
            [],
            ['HTTP_Authorization' => self::$accessToken]
        );

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $gift = json_decode($response->getContent(), true)[0];
        $this->assertSame(4, $gift['id']);
        $this->assertSame(12, $gift['playerId']);
        $this->assertSame('claimed', $gift['status']);
        $this->assertSame(2, $gift['reasonId']);
        $this->assertSame('2026-09-22 10:15:00', $gift['createdAt']);
        $this->assertSame('2026-09-22 10:15:00', $gift['updatedAt']);
        $query = QueryAwareMockClient::getLastRequestQuery('get', self::PROMOTION_GIFTS_PATH);
        $this->assertSame([7], $query['filter']['rewardConfigurationIds']);
        $this->assertArrayNotHasKey('ownerIds', $query['filter']);
        $this->assertSame(10, $query['limit']);
        $this->assertSame(20, $query['offset']);
        $this->assertSame(['field' => 'createdAt', 'direction' => 'desc'], $query['order']);
    }

    public function testListsAPromotionGiftOfAConfigurationWithItsPromotionAsTheCreator(): void
    {
        self::mockGetGifts(1, [self::promotionGiftRow(4, 12, ['sourceUserId' => null, 'sourcePromotionId' => 5])]);
        self::mockGetPromotionConfigurationsByIds(1, [['id' => 5, 'name' => 'VIP tier', 'status' => 'enabled']]);

        self::$client->request('GET', self::GIFTS_URL, ['filter' => ['rewardConfigurationIds' => [7]]], [], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $gift = json_decode($response->getContent(), true)[0];
        $this->assertSame(['id' => 5, 'name' => 'VIP tier'], $gift['createdBy']);
        $this->assertSame(5, $gift['sourcePromotionId']);
    }

    public function testDefaultsThePageOfTheConfigurationGifts(): void
    {
        QueryAwareMockClient::resetLastRequestQueries();
        self::mockGetGifts(1, []);

        self::$client->request('GET', self::GIFTS_URL, ['filter' => ['rewardConfigurationIds' => [7]]], [], ['HTTP_Authorization' => self::$accessToken]);

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
        $this->assertSame([], json_decode(self::$client->getResponse()->getContent(), true));
        $query = QueryAwareMockClient::getLastRequestQuery('get', self::PROMOTION_GIFTS_PATH);
        $this->assertSame(100, $query['limit']);
        $this->assertSame(0, $query['offset']);
    }

    /**
     * @param array<string, mixed> $query
     */
    #[DataProvider('invalidGiftsQueryProvider')]
    public function testRejectsAnInvalidGiftsQueryBeforeCallingPromotion(string $url, array $query): void
    {
        QueryAwareMockClient::resetLastRequestQueries();

        self::$client->request('GET', $url, $query, [], ['HTTP_Authorization' => self::$accessToken]);

        $this->assertSame(Response::HTTP_BAD_REQUEST, self::$client->getResponse()->getStatusCode());
        $this->assertNull(QueryAwareMockClient::getLastRequestQuery('get', self::PROMOTION_GIFTS_PATH));
        $this->assertNull(QueryAwareMockClient::getLastRequestQuery('get', self::PROMOTION_GIFTS_AGGREGATE_PATH));
    }

    public static function invalidGiftsQueryProvider(): Generator
    {
        yield 'list without configuration' => [self::GIFTS_URL, []];
        yield 'list with a zero configuration id' => [self::GIFTS_URL, ['filter' => ['rewardConfigurationIds' => [0]]]];
        yield 'list with a text configuration id' => [self::GIFTS_URL, ['filter' => ['rewardConfigurationIds' => ['abc']]]];
        yield 'count without configuration' => [
            self::GIFTS_COUNT_URL,
            ['aggregate' => ['aggregator' => 'count', 'field' => 'id']],
        ];
        yield 'count without aggregate' => [self::GIFTS_COUNT_URL, ['filter' => ['rewardConfigurationIds' => [7]]]];
    }

    public function testPreservesAPromotionErrorOnTheConfigurationGifts(): void
    {
        self::mockGetGiftsError(1, Response::HTTP_NOT_FOUND, ['message' => 'Not Found']);

        self::$client->request('GET', self::GIFTS_URL, ['filter' => ['rewardConfigurationIds' => [7]]], [], ['HTTP_Authorization' => self::$accessToken]);

        $this->assertSame(Response::HTTP_NOT_FOUND, self::$client->getResponse()->getStatusCode());
    }

    public function testCountsTheGiftsOfAConfiguration(): void
    {
        QueryAwareMockClient::resetLastRequestQueries();
        self::mockGetGiftsAggregate(1, 18);

        self::$client->request(
            'GET',
            self::GIFTS_COUNT_URL,
            ['filter' => ['rewardConfigurationIds' => [7]], 'aggregate' => ['aggregator' => 'count', 'field' => 'id']],
            [],
            ['HTTP_Authorization' => self::$accessToken]
        );

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
        $this->assertSame(['value' => 18], json_decode(self::$client->getResponse()->getContent(), true));
        $query = QueryAwareMockClient::getLastRequestQuery('get', self::PROMOTION_GIFTS_AGGREGATE_PATH);
        $this->assertSame([7], $query['filter']['rewardConfigurationIds']);
        $this->assertSame(['aggregator' => 'count', 'field' => 'id'], $query['aggregate']);
        $this->assertArrayNotHasKey('limit', $query);
    }

    public function testPreservesAPromotionErrorOnTheConfigurationGiftsCount(): void
    {
        self::mockV2Error(
            'GET',
            self::PROMOTION_HOST . '/api/domain/1/gifts/aggregate',
            Response::HTTP_NOT_FOUND,
            json_encode(['message' => 'Not Found'], JSON_THROW_ON_ERROR)
        );

        self::$client->request(
            'GET',
            self::GIFTS_COUNT_URL,
            ['filter' => ['rewardConfigurationIds' => [7]], 'aggregate' => ['aggregator' => 'count', 'field' => 'id']],
            [],
            ['HTTP_Authorization' => self::$accessToken]
        );

        $this->assertSame(Response::HTTP_NOT_FOUND, self::$client->getResponse()->getStatusCode());
    }
}
