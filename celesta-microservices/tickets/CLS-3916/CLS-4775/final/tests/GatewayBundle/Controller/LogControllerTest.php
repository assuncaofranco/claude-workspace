<?php

namespace Tests\GatewayBundle\Controller;

use Tests\GatewayBundle\ControllerTestCase;
use Tests\Support\QueryAwareMockClient;

class LogControllerTest extends ControllerTestCase
{
    public function testGetLogsFilterActionForwardsThePromotionSourceType(): void
    {
        self::mockGetUserActivities();
        QueryAwareMockClient::resetLastRequestQueries();

        self::$client->request('POST', '/api/gateway/logs', [
            'filter' => ['sourceTypes' => ['promotion'], 'sourceIds' => [5], 'domainIds' => [1]],
        ], [], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(200, $response->getStatusCode());
        $this->assertCount(2, json_decode($response->getContent(), true));
        $query = QueryAwareMockClient::getLastRequestQuery('get', 'api/user-activities');
        $this->assertSame(['promotion'], $query['filter']['sourceTypes']);
    }

    public function testGetLogsFilterCountActionForwardsThePromotionSourceType(): void
    {
        self::mockGetUserActivitiesAggregate();
        QueryAwareMockClient::resetLastRequestBodies();

        self::$client->request('POST', '/api/gateway/logs/count', [
            'filter' => ['sourceTypes' => ['promotion'], 'sourceIds' => [5], 'domainIds' => [1]],
        ], [], ['HTTP_Authorization' => self::$accessToken]);

        $response = self::$client->getResponse();
        $this->assertSame(200, $response->getStatusCode());
        $this->assertSame(21, json_decode($response->getContent(), true)['value']);
        $body = json_decode(QueryAwareMockClient::getLastRequestBody('post', 'api/user-activities/aggregate'), true);
        $this->assertSame(['promotion'], $body['filter']['sourceTypes']);
    }

    public function testGetLogsFilterActionReturnsActivityServiceErrors(): void
    {
        self::mockV2Error('GET', 'http://activityweb.docker/api/user-activities', 500);

        self::$client->request('POST', '/api/gateway/logs', [], [], [
            'HTTP_Authorization' => self::$accessToken,
        ]);

        $response = self::$client->getResponse();

        $this->assertSame(400, $response->getStatusCode());
        $this->assertSame(
            ['Internal Server Error', 'code' => 'VALIDATION_CONSTRAINT'],
            json_decode($response->getContent(), true)
        );
    }

    public function testGetLogsFilterCountActionRejectsInvalidLimit(): void
    {
        self::$client->request('POST', '/api/gateway/logs/count', ['limit' => 'ten'], [], [
            'HTTP_Authorization' => self::$accessToken,
        ]);

        $response = self::$client->getResponse();
        $responseContent = json_decode($response->getContent(), true);

        $this->assertSame(400, $response->getStatusCode());
        $this->assertSame('Validation Failed', $responseContent['message']);
        $this->assertSame(['Please enter an integer.'], $responseContent['errors']['children']['limit']['errors']);
    }
}
