<?php
namespace App\Models;

class Asset
{
    public function __construct(
        public int $id,
        public string $name,
        public string $type,
        public string $department = '',
        public string $owner = ''
    ) {}
}
