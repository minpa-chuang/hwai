<?php
namespace App\Models;

class Risk
{
    public function __construct(
        public int $assetId,
        public string $threat,
        public int $likelihood,
        public int $impact,
        public string $treatment = ''
    ) {}

    public function score(): int
    {
        return $this->likelihood * $this->impact;
    }
}
