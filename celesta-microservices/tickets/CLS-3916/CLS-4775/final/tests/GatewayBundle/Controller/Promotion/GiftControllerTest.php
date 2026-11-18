<?php

namespace Tests\GatewayBundle\Controller\Promotion;

use JobLibrary\Job\Activity\UserActivityJob;
use PHPUnit\Framework\Attributes\DataProvider;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Messenger\Envelope;
use Tests\GatewayBundle\ControllerTestCase;
use Tests\Support\QueryAwareMockClient;

class GiftControllerTest extends ControllerTestCase
{
    use GiftControllerTestTrait;

    public function testOmitsTheValueWhenNoneIsGiven(): void
    {
        self::mockGetPlayer();
        self::mockOfferGift();

        self::$client->jsonRequest(
            'POST',
            self::OFFER_URL,
            ['rewardConfigurationId' => 7],
            ['HTTP_Authorization' => self::$accessToken]
        );

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
        $forwarded = json_decode(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH), true);
        $this->assertSame(7, $forwarded['rewardConfigurationId']);
        $this->assertNull($forwarded['amount']);
    }

    public function testDispatchesOneGiftOfferedActivityOnAnOffer(): void
    {
        self::mockGetPlayer();
        self::mockOfferGift(1, 1, ['reasonId' => 4, 'reasonName' => 'Birthday']);
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => self::$accessToken]);

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
        $jobs = $this->sentGiftOfferedJobs();
        $this->assertCount(1, $jobs);
        $this->assertSame(UserActivityJob::SOURCE_TYPE_USER, $jobs[0]->getSourceType());
        $this->assertSame(1, $jobs[0]->getSourceUserId());
        $additionalData = $jobs[0]->getAdditionalData();
        $this->assertSame(1, $additionalData['player_id']);
        $this->assertSame(1, $additionalData['domain_id']);
        $this->assertSame(1, $additionalData['gift_id']);
        $this->assertSame(7, $additionalData['reward_configuration_id']);
        $this->assertSame('Birthday hamper', $additionalData['name']);
        $this->assertSame('150.50', $additionalData['value']);
        $this->assertSame('EUR', $additionalData['currency']);
        $this->assertArrayNotHasKey('quantity', $additionalData);
        $this->assertSame(4, $additionalData['reason_id']);
        $this->assertSame('Birthday', $additionalData['reason_name']);
        $this->assertSame('Handed over at the VIP dinner', $additionalData['description']);
    }

    public function testDispatchesNoActivityWhenPromotionRejectsTheOffer(): void
    {
        self::mockGetPlayer();
        self::mockOfferGiftError(1, 1, Response::HTTP_BAD_REQUEST, [
            'message' => 'Validation Failed',
            'errors' => ['rewardConfigurationId' => ['This reward configuration is disabled.']],
        ]);
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => self::$accessToken]);

        $this->assertSame(Response::HTTP_BAD_REQUEST, self::$client->getResponse()->getStatusCode());
        $this->assertSame([], $this->sentGiftOfferedJobs());
    }

    public function testRejectsAMissingRewardConfigurationBeforeCallingPromotion(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, ['value' => 10], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertNotEmpty($content['errors']['children']['rewardConfigurationId']['errors']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH));
        $this->assertSame([], $this->sentGiftOfferedJobs());
    }

    public function testRejectsTheRemovedNameAndCurrencyFields(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();

        $payload = self::PAYLOAD;
        $payload['name'] = 'Birthday hamper';
        $payload['currency'] = 'EUR';
        self::$client->jsonRequest('POST', self::OFFER_URL, $payload, ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertNotEmpty(json_decode($response->getContent(), true)['errors']['errors']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH));
    }

    public function testReturnsANullReasonWhenPromotionOmitsIt(): void
    {
        self::mockGetPlayer();
        self::mockOfferGift();

        $payload = self::PAYLOAD;
        unset($payload['reasonId']);
        self::$client->jsonRequest('POST', self::OFFER_URL, $payload, ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $this->assertNull($content['reasonId']);
        $this->assertNull($content['reason']);
    }

    public function testAcceptsAndIgnoresTheLegacyReason(): void
    {
        self::mockGetPlayer();
        self::mockOfferGift();

        $payload = self::PAYLOAD;
        unset($payload['reasonId']);
        $payload['reason'] = str_repeat('a', 65);
        self::$client->jsonRequest('POST', self::OFFER_URL, $payload, ['HTTP_Authorization' => self::$accessToken]);

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
        $forwarded = json_decode(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH), true);
        $this->assertNull($forwarded['reasonId']);
        $this->assertArrayNotHasKey('reason', $forwarded);
    }

    public function testRejectsANonPositiveReasonIdBeforeCallingPromotion(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();

        $payload = self::PAYLOAD;
        $payload['reasonId'] = 0;
        self::$client->jsonRequest('POST', self::OFFER_URL, $payload, ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertNotEmpty($content['errors']['children']['reasonId']['errors']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH));
    }

    public function testMapsAPromotionReasonIdErrorOntoTheForm(): void
    {
        self::mockGetPlayer();
        self::mockOfferGiftError(1, 1, Response::HTTP_BAD_REQUEST, [
            'message' => 'Validation Failed',
            'errors' => ['reasonId' => ['This reason does not exist.']],
        ]);

        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['errors' => ['This reason does not exist.']], $content['errors']['children']['reasonId']);
    }

    public function testMapsAPromotionRewardConfigurationErrorOntoTheForm(): void
    {
        self::mockGetPlayer();
        self::mockOfferGiftError(1, 1, Response::HTTP_BAD_REQUEST, [
            'message' => 'Validation Failed',
            'errors' => ['rewardConfigurationId' => ["This reward configuration is disabled."]],
        ]);

        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['errors' => ['This reward configuration is disabled.']], $content['errors']['children']['rewardConfigurationId']);
    }

    public function testMapsAPromotionAmountErrorOntoTheValueField(): void
    {
        self::mockGetPlayer();
        self::mockOfferGiftError(1, 1, Response::HTTP_BAD_REQUEST, [
            'message' => 'Validation Failed',
            'errors' => ['amount' => ['This value should have at most two decimals.']],
        ]);

        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['errors' => ['This value should have at most two decimals.']], $content['errors']['children']['value']);
    }

    public function testPreservesAPromotionNotFoundOnTheOffer(): void
    {
        self::mockGetPlayer();
        self::mockOfferGiftError(1, 1, Response::HTTP_NOT_FOUND, ['code' => 404, 'errors' => ['Domain not found']]);

        self::$client->jsonRequest(
            'POST',
            self::OFFER_URL,
            self::PAYLOAD,
            ['HTTP_Authorization' => self::$accessToken]
        );

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_NOT_FOUND, $response->getStatusCode());
        $this->assertSame(
            ['message' => 'Not Found', 'code' => 'NOT_FOUND'],
            json_decode($response->getContent(), true)
        );
    }

    public function testReportsAPromotionServerErrorOnTheOfferAsABadRequest(): void
    {
        self::mockGetPlayer();
        self::mockOfferGiftError(1, 1, Response::HTTP_INTERNAL_SERVER_ERROR, ['errors' => 'Internal Server Error']);

        self::$client->jsonRequest(
            'POST',
            self::OFFER_URL,
            self::PAYLOAD,
            ['HTTP_Authorization' => self::$accessToken]
        );

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(
            ['Internal Server Error', 'code' => 'VALIDATION_CONSTRAINT'],
            json_decode($response->getContent(), true)
        );
    }

    public function testRejectsAPlayerWithAnInvalidStatus(): void
    {
        self::mockGetLockedCustomer();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertNotEmpty($content['errors']['errors']);
    }

    public function testRejectsAnInvalidPayloadBeforeCallingPromotion(): void
    {
        self::$client->jsonRequest('POST', self::OFFER_URL, ['rewardConfigurationId' => 0, 'value' => -1], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertNotEmpty($content['errors']['children']['rewardConfigurationId']);
        $this->assertNotEmpty($content['errors']['children']['value']);
    }

    public function testRejectsAQuantityAsAnExtraField(): void
    {
        self::$client->jsonRequest(
            'POST',
            self::OFFER_URL,
            ['rewardConfigurationId' => 7, 'quantity' => 2],
            ['HTTP_Authorization' => self::$accessToken]
        );

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['This form should not contain extra fields.'], $content['errors']['errors']);
    }

    public function testOffersDirectlyWithOnlyTheOfferPermission(): void
    {
        $this->assertOffersDirectly(self::$offerOnlyAccessToken);
    }

    public function testOffersDirectlyWhenBothPermissionsAreHeld(): void
    {
        $this->assertOffersDirectly(self::$offerAndRequestAccessToken);
    }

    public function testRequestsAGiftWithOnlyTheRequestPermission(): void
    {
        self::mockGetPlayer();
        self::mockPostGiftRequest();
        QueryAwareMockClient::resetLastRequestBodies();
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::REQUEST_PAYLOAD, ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $this->assertSame('requested', $content['status']);
        $this->assertSame('150.50', $content['value']);
        $this->assertArrayNotHasKey('amount', $content);
        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $content['requestedBy']);
        $this->assertNull($content['approvedBy']);
        $this->assertNull($content['rejectedBy']);

        $forwarded = json_decode(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_REQUEST_PATH), true);
        $this->assertSame(['rewardConfigurationId', 'amount', 'description', 'reasonId', 'requestedByUserId'], array_keys($forwarded));
        $this->assertSame(7, $forwarded['rewardConfigurationId']);
        $this->assertSame('150.5', $forwarded['amount']);
        $this->assertSame('Handed over at the VIP dinner', $forwarded['description']);
        $this->assertSame(4, $forwarded['reasonId']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH));

        $jobs = $this->sentJobs(UserActivityJob::EVENT_GIFT_REQUESTED);
        $this->assertCount(1, $jobs);
        $this->assertSame([], $this->sentGiftOfferedJobs());
        $this->assertSame($forwarded['requestedByUserId'], $jobs[0]->getSourceUserId());
        $this->assertSame(UserActivityJob::SOURCE_TYPE_USER, $jobs[0]->getSourceType());
        $this->assertSame([
            'player_id' => 1,
            'domain_id' => 1,
            'company_id' => 1,
            'gift_request_id' => 12,
            'reward_configuration_id' => 7,
            'name' => 'Birthday hamper',
            'value' => '150.50',
            'currency' => 'EUR',
            'reason_id' => 4,
            'reason_name' => 'Birthday',
            'description' => 'Handed over at the VIP dinner',
        ], $jobs[0]->getAdditionalData());
    }

    public function testForbiddenWithNeitherTheOfferNorTheRequestPermission(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::REQUEST_PAYLOAD, ['HTTP_Authorization' => self::$restrictedAccessToken]);

        $this->assertSame(Response::HTTP_FORBIDDEN, self::$client->getResponse()->getStatusCode());
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_REQUEST_PATH));
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH));
        $this->assertSame([], $this->sentJobs(UserActivityJob::EVENT_GIFT_REQUESTED));
        $this->assertSame([], $this->sentGiftOfferedJobs());
    }

    public function testRejectsAQuantityAsAnExtraFieldOnTheRequestPath(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, ['quantity' => 1] + self::REQUEST_PAYLOAD, ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['This form should not contain extra fields.'], $content['errors']['errors']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_REQUEST_PATH));
        $this->assertSame([], $this->sentJobs(UserActivityJob::EVENT_GIFT_REQUESTED));
    }

    public function testSendsANullAmountWhenTheRequestHasNoValue(): void
    {
        self::mockGetPlayer();
        self::mockPostGiftRequest();

        self::$client->jsonRequest('POST', self::OFFER_URL, ['rewardConfigurationId' => 7], ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
        $forwarded = json_decode(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_REQUEST_PATH), true);
        $this->assertNull($forwarded['amount']);
        $this->assertNull($forwarded['description']);
        $this->assertNull($forwarded['reasonId']);
    }

    public function testRejectsAnInvalidPlayerStatusOnTheRequestPath(): void
    {
        self::mockGetLockedCustomer();
        QueryAwareMockClient::resetLastRequestBodies();
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::REQUEST_PAYLOAD, ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertNotEmpty(json_decode($response->getContent(), true)['errors']['errors']);
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_REQUEST_PATH));
        $this->assertSame([], $this->sentJobs(UserActivityJob::EVENT_GIFT_REQUESTED));
    }

    public function testRejectsAnInvalidRequestPayloadBeforeCallingPromotion(): void
    {
        QueryAwareMockClient::resetLastRequestBodies();

        self::$client->jsonRequest('POST', self::OFFER_URL, ['value' => 10], ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $this->assertSame(Response::HTTP_BAD_REQUEST, self::$client->getResponse()->getStatusCode());
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_REQUEST_PATH));
    }

    public function testMapsAPromotionAmountErrorOntoTheValueFieldOnTheRequestPath(): void
    {
        self::mockGetPlayer();
        self::mockPostGiftRequestError(1, 1, Response::HTTP_BAD_REQUEST, [
            'message' => 'Validation Failed',
            'errors' => ['amount' => ['This value should have at most two decimals.']],
            'code' => 'VALIDATION_CONSTRAINT',
        ]);
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::REQUEST_PAYLOAD, ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $response = self::$client->getResponse();
        $content = json_decode($response->getContent(), true);
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['errors' => ['This value should have at most two decimals.']], $content['errors']['children']['value']);
        $this->assertSame([], $this->sentJobs(UserActivityJob::EVENT_GIFT_REQUESTED));
    }

    #[DataProvider('passedThroughPromotionErrorProvider')]
    public function testPassesPromotionErrorsOnTheRequestPathThroughAsPromotionSentThem(int $status, array $body): void
    {
        self::mockGetPlayer();
        self::mockPostGiftRequestError(1, 1, $status, $body);
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::REQUEST_PAYLOAD, ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $response = self::$client->getResponse();
        $this->assertSame($status, $response->getStatusCode());
        $this->assertSame($body, json_decode($response->getContent(), true));
        $this->assertSame([], $this->sentJobs(UserActivityJob::EVENT_GIFT_REQUESTED));
    }

    public static function passedThroughPromotionErrorProvider(): \Generator
    {
        yield 'currency mismatch' => [Response::HTTP_BAD_REQUEST, ['code' => 'CURRENCY_MISMATCH', 'message' => 'The player holds no EUR wallet.']];
        yield 'upstream unavailable' => [Response::HTTP_SERVICE_UNAVAILABLE, ['code' => 'UPSTREAM_UNAVAILABLE', 'message' => 'The wallet is unavailable.']];
    }

    public function testPreservesAPromotionPlayerNotFoundOnTheRequestPath(): void
    {
        self::mockGetPlayer();
        self::mockPostGiftRequestError(1, 1, Response::HTTP_NOT_FOUND, ['code' => 'PLAYER_NOT_FOUND', 'message' => 'Player not found']);
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::REQUEST_PAYLOAD, ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_NOT_FOUND, $response->getStatusCode());
        $this->assertSame(['message' => 'Not Found', 'code' => 'NOT_FOUND'], json_decode($response->getContent(), true));
        $this->assertSame([], $this->sentJobs(UserActivityJob::EVENT_GIFT_REQUESTED));
    }

    public function testReportsAPromotionServerErrorOnTheRequestPathAsABadRequest(): void
    {
        self::mockGetPlayer();
        self::mockPostGiftRequestError(1, 1, Response::HTTP_INTERNAL_SERVER_ERROR, ['errors' => 'Internal Server Error']);

        self::$client->jsonRequest('POST', self::OFFER_URL, self::REQUEST_PAYLOAD, ['HTTP_Authorization' => self::$requestOnlyAccessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_BAD_REQUEST, $response->getStatusCode());
        $this->assertSame(['Internal Server Error', 'code' => 'VALIDATION_CONSTRAINT'], json_decode($response->getContent(), true));
    }

    private function assertOffersDirectly(string $accessToken): void
    {
        self::mockGetPlayer();
        self::mockOfferGift();
        QueryAwareMockClient::resetLastRequestBodies();
        $this->resetActivityTransport();

        self::$client->jsonRequest('POST', self::OFFER_URL, self::PAYLOAD, ['HTTP_Authorization' => $accessToken]);

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
        $this->assertSame('claimed', json_decode(self::$client->getResponse()->getContent(), true)['status']);
        $this->assertNotNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_OFFER_PATH));
        $this->assertNull(QueryAwareMockClient::getLastRequestBody('post', self::PROMOTION_REQUEST_PATH));
        $this->assertCount(1, $this->sentGiftOfferedJobs());
        $this->assertSame([], $this->sentJobs(UserActivityJob::EVENT_GIFT_REQUESTED));
    }

    public function testListsThePlayerGiftsNormalized(): void
    {
        self::mockGetGifts(1, [
            self::promotionGiftRow(2, 1, ['name' => 'Watch', 'amount' => '300.00', 'description' => null, 'reasonId' => 2, 'reasonName' => 'Christmas', 'createdAt' => '2026-09-22 12:00:00']),
            self::promotionGiftRow(1, 1),
        ]);

        self::$client->request(
            'GET',
            self::LIST_URL,
            ['limit' => 2, 'offset' => 0, 'order' => ['field' => 'createdAt', 'direction' => 'desc']],
            [],
            ['HTTP_Authorization' => self::$accessToken]
        );

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $this->assertSame([
            [
                'id' => 2,
                'playerId' => 1,
                'status' => 'claimed',
                'name' => 'Watch',
                'value' => '300.00',
                'currency' => 'EUR',
                'rewardConfigurationId' => 7,
                'description' => null,
                'reasonId' => 2,
                'reason' => 'Christmas',
                'createdBy' => ['id' => 1, 'name' => 'Marta Kulas'],
                'sourceScenarioId' => null,
                'sourcePromotionId' => null,
                'createdAt' => '2026-09-22 12:00:00',
                'updatedAt' => '2026-09-22 10:15:00',
                'giftRequestId' => null,
                'requestedAt' => null,
                'approvedAt' => null,
                'requestedBy' => null,
                'approvedBy' => null,
            ],
            [
                'id' => 1,
                'playerId' => 1,
                'status' => 'claimed',
                'name' => 'Birthday hamper',
                'value' => '150.50',
                'currency' => 'EUR',
                'rewardConfigurationId' => 7,
                'description' => 'Handed over at the VIP dinner',
                'reasonId' => null,
                'reason' => null,
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
            ],
        ], json_decode($response->getContent(), true));
    }

    public function testListsAScenarioGiftWithItsScenarioAndNoCreator(): void
    {
        self::mockGetGifts(1, [
            self::promotionGiftRow(3, 1, ['sourceUserId' => null, 'sourceScenarioId' => 12]),
        ]);

        self::$client->request('GET', self::LIST_URL, [], [], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $this->assertSame([
            [
                'id' => 3,
                'playerId' => 1,
                'status' => 'claimed',
                'name' => 'Birthday hamper',
                'value' => '150.50',
                'currency' => 'EUR',
                'rewardConfigurationId' => 7,
                'description' => 'Handed over at the VIP dinner',
                'reasonId' => null,
                'reason' => null,
                'createdBy' => null,
                'sourceScenarioId' => 12,
                'sourcePromotionId' => null,
                'createdAt' => '2026-09-22 10:15:00',
                'updatedAt' => '2026-09-22 10:15:00',
                'giftRequestId' => null,
                'requestedAt' => null,
                'approvedAt' => null,
                'requestedBy' => null,
                'approvedBy' => null,
            ],
        ], json_decode($response->getContent(), true));
    }

    public function testListsAPromotionGiftWithItsPromotionAsTheCreator(): void
    {
        QueryAwareMockClient::resetLastRequestQueries();
        self::mockGetGifts(1, [
            self::promotionGiftRow(5, 1, ['sourceUserId' => null, 'sourcePromotionId' => 5]),
            self::promotionGiftRow(1, 1),
        ]);
        self::mockGetPromotionConfigurationsByIds(1, [
            ['id' => 5, 'name' => 'VIP tier', 'status' => 'disabled'],
        ]);

        self::$client->request('GET', self::LIST_URL, [], [], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $gifts = json_decode($response->getContent(), true);
        $this->assertSame(['id' => 5, 'name' => 'VIP tier'], $gifts[0]['createdBy']);
        $this->assertSame(5, $gifts[0]['sourcePromotionId']);
        $this->assertNull($gifts[0]['sourceScenarioId']);
        $this->assertSame(['id' => 1, 'name' => 'Marta Kulas'], $gifts[1]['createdBy']);
        $this->assertNull($gifts[1]['sourcePromotionId']);
        $query = QueryAwareMockClient::getLastRequestQuery('get', 'api/domain/1/promotion-configurations');
        $this->assertSame(['ids' => [5]], $query['filter']);
        $this->assertSame(1, $query['limit']);
        $this->assertSame(0, $query['offset']);
    }

    public function testListsAPromotionGiftWithNoCreatorWhenPromotionConfigurationsCannotBeFetched(): void
    {
        self::mockGetGifts(1, [self::promotionGiftRow(5, 1, ['sourceUserId' => null, 'sourcePromotionId' => 5])]);
        self::mockV2Error('GET', self::PROMOTION_HOST . '/api/domain/1/promotion-configurations', Response::HTTP_INTERNAL_SERVER_ERROR);

        self::$client->request('GET', self::LIST_URL, [], [], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $gift = json_decode($response->getContent(), true)[0];
        $this->assertNull($gift['createdBy']);
        $this->assertSame(5, $gift['sourcePromotionId']);
    }

    public function testDoesNotLookUpPromotionConfigurationsWhenNoGiftComesFromAPromotion(): void
    {
        QueryAwareMockClient::resetLastRequestQueries();
        self::mockGetGifts(1, [self::promotionGiftRow(1, 1), self::promotionGiftRow(3, 1, ['sourceUserId' => null, 'sourceScenarioId' => 12])]);

        self::$client->request('GET', self::LIST_URL, [], [], ['HTTP_Authorization' => self::$accessToken]);

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
        $this->assertFalse(QueryAwareMockClient::wasRequested('get', 'api/domain/1/promotion-configurations'));
    }

    public function testReturnsAnEmptyListWhenThePlayerHasNoGift(): void
    {
        self::mockGetGifts(1, []);

        self::$client->request('GET', self::LIST_URL, [], [], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_OK, $response->getStatusCode());
        $this->assertSame([], json_decode($response->getContent(), true));
    }

    public function testAcceptsTheFrontValueSortKey(): void
    {
        self::mockGetGifts(1, [self::promotionGiftRow(1, 1)]);

        self::$client->request(
            'GET',
            self::LIST_URL,
            ['order' => ['field' => 'value', 'direction' => 'desc']],
            [],
            ['HTTP_Authorization' => self::$accessToken]
        );

        $this->assertSame(Response::HTTP_OK, self::$client->getResponse()->getStatusCode());
    }

    public function testRejectsAnUnknownOrderField(): void
    {
        self::$client->request(
            'GET',
            self::LIST_URL,
            ['order' => ['field' => 'description', 'direction' => 'asc']],
            [],
            ['HTTP_Authorization' => self::$accessToken]
        );

        $this->assertSame(Response::HTTP_BAD_REQUEST, self::$client->getResponse()->getStatusCode());
    }

    public function testPreservesAPromotionNotFoundOnTheList(): void
    {
        self::mockGetGiftsError(1, Response::HTTP_NOT_FOUND, ['code' => 404, 'errors' => ['Domain not found']]);

        self::$client->request('GET', self::LIST_URL, [], [], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(Response::HTTP_NOT_FOUND, $response->getStatusCode());
        $this->assertSame(['message' => 'Not Found', 'code' => 'NOT_FOUND'], json_decode($response->getContent(), true));
    }

    public function testRejectsALimitAboveTheMaximum(): void
    {
        self::$client->request('GET', self::LIST_URL, ['limit' => 501], [], ['HTTP_Authorization' => self::$accessToken]);

        $this->assertSame(Response::HTTP_BAD_REQUEST, self::$client->getResponse()->getStatusCode());
    }

    private function resetActivityTransport(): void
    {
        self::getContainer()->get('messenger.transport.activity_sqs_kubernetes')->reset();
    }

    /**
     * @return list<UserActivityJob>
     */
    private function sentGiftOfferedJobs(): array
    {
        return $this->sentJobs(UserActivityJob::EVENT_GIFT_OFFERED);
    }

    /**
     * @return list<UserActivityJob>
     */
    private function sentJobs(string $event): array
    {
        $transport = self::getContainer()->get('messenger.transport.activity_sqs_kubernetes');

        return array_values(array_filter(
            array_map(static fn (Envelope $envelope): object => $envelope->getMessage(), $transport->getSent()),
            static fn (object $message): bool => $message instanceof UserActivityJob
                && $message->getEvent() === $event
        ));
    }
}
