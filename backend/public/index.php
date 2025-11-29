<?php

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

try {
    $app = require __DIR__ . '/../bootstrap.php';

    /** @var \Hwai\Http\Router $router */
    $router = $app->get(\Hwai\Http\Router::class);

    $payload = $router->healthCheck();

    http_response_code(200);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
} catch (\Throwable $throwable) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Server initialization failed.',
        'exception' => [
            'type' => $throwable::class,
            'message' => $throwable->getMessage(),
        ],
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
}
