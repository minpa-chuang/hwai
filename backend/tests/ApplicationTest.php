<?php

declare(strict_types=1);

use Hwai\Application;
use PHPUnit\Framework\TestCase;

class ApplicationTest extends TestCase
{
    public function testStoresAndResolvesConcreteValues(): void
    {
        $app = new Application();
        $app->set('config', ['db' => 'mariadb']);

        $this->assertSame(['db' => 'mariadb'], $app->get('config'));
    }

    public function testResolvesClosureOnlyOnce(): void
    {
        $app = new Application();
        $app->set('time', static function () {
            return microtime(true);
        });

        $first = $app->get('time');
        $second = $app->get('time');

        $this->assertIsFloat($first);
        $this->assertSame($first, $second);
    }

    public function testThrowsWhenServiceNotRegistered(): void
    {
        $app = new Application();

        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage("Service 'missing' is not registered in the container.");

        $app->get('missing');
    }
}
