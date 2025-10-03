-- 工作日誌與維修管理系統 Schema
-- 對應功能需求規格書 v2.3

SET NAMES utf8mb4;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'STRICT_ALL_TABLES';

CREATE TABLE IF NOT EXISTS `departments` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '部門ID',
  `name` VARCHAR(100) NOT NULL COMMENT '部門名稱',
  `parent_id` INT UNSIGNED DEFAULT NULL COMMENT '上級部門ID (NULL為一級部門)',
  PRIMARY KEY (`id`),
  KEY `idx_parent_id` (`parent_id`),
  CONSTRAINT `fk_parent_dept` FOREIGN KEY (`parent_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部門資料表';

CREATE TABLE IF NOT EXISTS `users` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '使用者ID',
  `username` VARCHAR(50) NOT NULL COMMENT '登入帳號',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '雜湊後的密碼',
  `full_name` VARCHAR(50) NOT NULL COMMENT '使用者全名',
  `email` VARCHAR(255) NOT NULL COMMENT '電子郵件',
  `role` ENUM('admin', 'repairer') NOT NULL DEFAULT 'repairer' COMMENT '使用者角色',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='使用者資料表';

CREATE TABLE IF NOT EXISTS `maintenance_records` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '記錄ID',
  `record_date` DATE NOT NULL COMMENT '報修日期',
  `department_id` INT UNSIGNED NOT NULL COMMENT '報修部門ID',
  `user_id` INT UNSIGNED DEFAULT NULL COMMENT '負責維修人員ID',
  `reporter_name` VARCHAR(50) NOT NULL COMMENT '報修人姓名',
  `issue_description` TEXT NOT NULL COMMENT '問題需求描述',
  `solution_description` TEXT COMMENT '處理過程描述',
  `time_spent_minutes` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '花費時間(分鐘)',
  `status` ENUM('待處理', '處理中', '已完成', '待料') NOT NULL DEFAULT '待處理' COMMENT '案件狀態',
  `priority` ENUM('低', '中', '高', '緊急') NOT NULL DEFAULT '中' COMMENT '優先級',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '記錄建立時間',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '記錄更新時間',
  PRIMARY KEY (`id`),
  KEY `idx_record_date` (`record_date`),
  KEY `idx_department_id` (`department_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_priority` (`priority`),
  CONSTRAINT `fk_record_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_record_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='維修記錄資料表';

CREATE TABLE IF NOT EXISTS `password_resets` (
  `email` VARCHAR(255) NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`email`),
  KEY `idx_token` (`token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='密碼重設權杖表';

CREATE TABLE IF NOT EXISTS `tags` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='維修案件分類標籤';

CREATE TABLE IF NOT EXISTS `maintenance_record_tags` (
  `record_id` INT UNSIGNED NOT NULL,
  `tag_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`record_id`, `tag_id`),
  CONSTRAINT `fk_rt_record` FOREIGN KEY (`record_id`) REFERENCES `maintenance_records` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_rt_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='維修記錄與標籤關聯表';

CREATE TABLE IF NOT EXISTS `attachments` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `record_id` INT UNSIGNED NOT NULL,
  `original_filename` VARCHAR(255) NOT NULL,
  `stored_path` VARCHAR(255) NOT NULL,
  `file_type` VARCHAR(100) NOT NULL,
  `file_size` INT UNSIGNED NOT NULL,
  `uploaded_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_attach_record` FOREIGN KEY (`record_id`) REFERENCES `maintenance_records` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='附件資料表';

CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED DEFAULT NULL,
  `action` VARCHAR(255) NOT NULL,
  `target_type` VARCHAR(50) DEFAULT NULL,
  `target_id` INT UNSIGNED DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_action` (`user_id`, `action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='稽核日誌資料表';

SET foreign_key_checks = 1;
