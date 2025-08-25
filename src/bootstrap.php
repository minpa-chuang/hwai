<?php
spl_autoload_register(function($class){
    $prefix = 'App\\';
    $base_dir = __DIR__ . '/';
    if(strpos($class, $prefix) === 0){
        $relative = str_replace('\\', '/', substr($class, strlen($prefix)));
        $file = $base_dir . $relative . '.php';
        if(file_exists($file)) require $file;
    }
});
