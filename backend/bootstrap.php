<?php

declare(strict_types=1);

use Hwai\Support\Env;
use Hwai\Application;
use Hwai\Http\Router;

$autoloadPath = __DIR__ . '/../vendor/autoload.php';
if (file_exists($autoloadPath)) {
    require_once $autoloadPath;
} else {
    spl_autoload_register(static function (string $class): void {
        $prefix = 'Hwai\\';
        $baseDir = __DIR__ . '/src/';

        if (!str_starts_with($class, $prefix)) {
            return;
        }

        $relativeClass = substr($class, strlen($prefix));
        $file = $baseDir . str_replace('\\', '/', $relativeClass) . '.php';

        if (file_exists($file)) {
            require $file;
        }
    });
}

// 載入環境變數
$envPath = dirname(__DIR__) . '/.env';
if (is_readable($envPath)) {
    Env::load($envPath);
}

// 建立應用程式容器
$app = new Application();
$app->set('config.database', require __DIR__ . '/config/database.php');

// 註冊路由器 (後續可替換為專業框架)
$app->set(Router::class, function (): Router {
    return new Router();
});

return $app;
