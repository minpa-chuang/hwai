<?php

declare(strict_types=1);

namespace Hwai;

/**
 * 簡易的服務容器，提供設定與擴充性。
 * 後續可替換為完整的框架容器 (如 Laravel Service Container)。
 */
class Application
{
    /** @var array<string, mixed> */
    private array $bindings = [];

    /** @var array<string, mixed> */
    private array $instances = [];

    /**
     * 以鍵值註冊服務或設定。
     *
     * @param string $key
     * @param mixed $value
     */
    public function set(string $key, mixed $value): void
    {
        $this->bindings[$key] = $value;
    }

    /**
     * 取得服務或設定。
     * 如果綁定的是 Closure，會自動延後載入並快取實例。
     *
     * @param string $key
     * @return mixed
     */
    public function get(string $key): mixed
    {
        if (array_key_exists($key, $this->instances)) {
            return $this->instances[$key];
        }

        if (!array_key_exists($key, $this->bindings)) {
            throw new \InvalidArgumentException("Service '{$key}' is not registered in the container.");
        }

        $value = $this->bindings[$key];
        if ($value instanceof \Closure) {
            $value = $value($this);
        }

        $this->instances[$key] = $value;

        return $value;
    }
}
