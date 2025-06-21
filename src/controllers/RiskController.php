<?php
namespace App\Controllers;
use App\Models\Risk;

class RiskController
{
    private static array $risks = [];

    public static function list(): string
    {
        $scores = array_map(fn($r)=>['assetId'=>$r->assetId,'score'=>$r->score()], self::$risks);
        return json_encode($scores, JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE);
    }

    public static function add(int $assetId, string $threat, int $likelihood, int $impact): void
    {
        self::$risks[] = new Risk($assetId, $threat, $likelihood, $impact);
    }
}
