<?php

declare(strict_types=1);

namespace Hwai\Http;

/**
 * 極簡路由器：後續會被更完整的框架或自訂實作取代。
 * 目前僅用於確認專案初始化流程正常。
 */
class Router
{
    /**
     * 目前僅回傳靜態的健康檢查資訊。
     *
     * @return array<string, mixed>
     */
    public function healthCheck(): array
    {
        return [
            'status' => 'ok',
            'timestamp' => (new \DateTimeImmutable())->format(DATE_ATOM),
        ];
    }
}
