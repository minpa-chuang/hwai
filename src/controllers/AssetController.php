<?php
namespace App\Controllers;
use App\Models\Asset;

class AssetController
{
    private static array $assets = [];

    public static function list(): string
    {
        return json_encode(array_values(self::$assets), JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE);
    }

    public static function add(): string
    {
        $id = count(self::$assets) + 1;
        $name = $_POST['name'] ?? 'unknown';
        $type = $_POST['type'] ?? 'other';
        $asset = new Asset($id, $name, $type);
        self::$assets[$id] = $asset;
        return json_encode(['added' => $asset], JSON_UNESCAPED_UNICODE);
    }
}
