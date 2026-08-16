-- ============================================================
-- CounterGuard Database Schema
-- ============================================================
-- Run with:  mysql -u root -p < database.sql
-- Or paste into MySQL Workbench / phpMyAdmin.
-- ============================================================

CREATE DATABASE IF NOT EXISTS counterguard_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE counterguard_db;

-- ------------------------------------------------------------
-- Table: users  (customer accounts)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(100)    NOT NULL,
    username        VARCHAR(50)     NOT NULL UNIQUE,
    email           VARCHAR(120)    NOT NULL UNIQUE,
    phone           VARCHAR(20)     DEFAULT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: admins  (admin portal accounts — kept separate from
-- customers so admin auth and customer auth never share a
-- session/role namespace)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(100)    NOT NULL,
    username        VARCHAR(50)     NOT NULL UNIQUE,
    email           VARCHAR(120)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    role            ENUM('super_admin', 'admin') NOT NULL DEFAULT 'admin',
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: products
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(150)    NOT NULL,
    brand               VARCHAR(100)    NOT NULL,
    category            VARCHAR(80)     DEFAULT NULL,
    description         TEXT            DEFAULT NULL,
    manufacturer        VARCHAR(150)    DEFAULT NULL,
    barcode_value       VARCHAR(64)     NOT NULL UNIQUE,
    barcode_image_path  VARCHAR(255)    DEFAULT NULL,
    product_image_path  VARCHAR(255)    DEFAULT NULL,
    price               DECIMAL(10,2)   DEFAULT NULL,
    manufacture_date    DATE            DEFAULT NULL,
    expiry_date         DATE            DEFAULT NULL,
    status              ENUM('active','discontinued') NOT NULL DEFAULT 'active',
    created_by          INT             DEFAULT NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_creator FOREIGN KEY (created_by)
        REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_barcode_value (barcode_value)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: scans  (every verification attempt, found or not)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scans (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT             DEFAULT NULL,
    product_id      INT             DEFAULT NULL,
    barcode_value   VARCHAR(64)     NOT NULL,
    result_status   ENUM('genuine','not_found') NOT NULL,
    ip_address      VARCHAR(45)     DEFAULT NULL,
    scanned_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_scan_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_scan_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_scan_barcode (barcode_value),
    INDEX idx_scan_user (user_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: reports  (customer reports of suspected counterfeits)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT             NOT NULL,
    product_id      INT             DEFAULT NULL,
    barcode_value   VARCHAR(64)     NOT NULL,
    description     TEXT            NOT NULL,
    evidence_image  VARCHAR(255)    DEFAULT NULL,
    status          ENUM('pending','reviewed','resolved','rejected')
                                    NOT NULL DEFAULT 'pending',
    reviewed_by     INT             DEFAULT NULL,
    admin_notes     TEXT            DEFAULT NULL,
    reported_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at     DATETIME        DEFAULT NULL,
    CONSTRAINT fk_report_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_report_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE SET NULL,
    CONSTRAINT fk_report_admin FOREIGN KEY (reviewed_by)
        REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_report_status (status)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Seed: one default admin account.
-- Password hash below corresponds to plaintext "Admin@12345"
-- generated with Werkzeug's generate_password_hash().
-- Change this immediately after first login in a real deployment,
-- or better, use scripts/seed_admin.py which hashes from .env.
-- ------------------------------------------------------------
-- INSERT INTO admins (full_name, username, email, password_hash, role)
-- VALUES ('System Administrator', 'admin', 'admin@counterguard.local',
--         '<generated-hash-goes-here>', 'super_admin');
