<?php

declare(strict_types=1);

use Hwai\Support\Env;
use PHPUnit\Framework\TestCase;

class EnvTest extends TestCase
{
    private string $envFile;

    protected function setUp(): void
    {
        $this->envFile = tempnam(sys_get_temp_dir(), 'env');
    }

    protected function tearDown(): void
    {
        if ($this->envFile !== '' && file_exists($this->envFile)) {
            unlink($this->envFile);
        }

        putenv('APP_NAME');
        unset($_ENV['APP_NAME'], $_SERVER['APP_NAME']);
    }

    public function testLoadSetsEnvironmentValues(): void
    {
        file_put_contents($this->envFile, "APP_NAME=Maintenance\n# Comment\nEMPTY=\n");

        Env::load($this->envFile);

        $this->assertSame('Maintenance', getenv('APP_NAME'));
        $this->assertSame('Maintenance', $_ENV['APP_NAME']);
        $this->assertNull(Env::get('EMPTY'));
    }

    public function testGetReturnsDefaultWhenMissing(): void
    {
        $this->assertNull(Env::get('UNKNOWN'));
        $this->assertSame('fallback', Env::get('UNKNOWN', 'fallback'));
    }
}
