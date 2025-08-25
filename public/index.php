<?php
require_once __DIR__.'/../src/bootstrap.php';
use App\Controllers\AssetController;
use App\Controllers\RiskController;

$action = $_GET['action'] ?? 'home';
$controller = match($action) {
    'list_assets' => [AssetController::class, 'list'],
    'add_asset'   => [AssetController::class, 'add'],
    'list_risks'  => [RiskController::class, 'list'],
    default       => null,
};

if ($controller) {
    echo call_user_func($controller);
} else {
    echo "ISMS Management API";
}
