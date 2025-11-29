<?php

declare(strict_types=1);

use Hwai\Http\Router;
use PHPUnit\Framework\TestCase;

class RouterTest extends TestCase
{
    public function testHealthCheckReturnsStatusAndTimestamp(): void
    {
        $router = new Router();

        $response = $router->healthCheck();

        $this->assertSame('ok', $response['status']);
        $this->assertArrayHasKey('timestamp', $response);
        $this->assertNotEmpty($response['timestamp']);
    }
}
