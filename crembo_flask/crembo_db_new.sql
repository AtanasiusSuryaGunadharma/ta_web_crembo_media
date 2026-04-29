-- MySQL schema for Crembo legacy migration

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

CREATE TABLE IF NOT EXISTS `anggota` (
  `id` int(11) NOT NULL,
  `nama` varchar(255) DEFAULT NULL,
  `username` varchar(150) DEFAULT NULL,
  `telp` varchar(50) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(50) DEFAULT NULL,
  `tgl_lahir` varchar(50) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_anggota_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `db_anggota` (
  `id` int(11) NOT NULL,
  `nama` varchar(255) DEFAULT NULL,
  `username` varchar(150) DEFAULT NULL,
  `telp` varchar(50) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `kegiatan` (
  `id` int(11) NOT NULL,
  `judul` varchar(255) NOT NULL,
  `tanggal` varchar(50) NOT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'draft',
  `misa_json` longtext NOT NULL,
  `created_at` varchar(50) NOT NULL,
  `updated_at` varchar(50) NOT NULL,
  `misa_ke` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `kegiatan_form` (
  `id` int(11) NOT NULL,
  `judul` varchar(255) DEFAULT NULL,
  `slug` varchar(255) DEFAULT NULL,
  `jumlah_hari` int(11) DEFAULT NULL,
  `jumlah_misa` int(11) DEFAULT NULL,
  `jml_kamera` int(11) DEFAULT NULL,
  `jml_supervisor` int(11) DEFAULT NULL,
  `jml_fotografer` int(11) DEFAULT NULL,
  `misa_terakhir` date DEFAULT NULL,
  `form_json` longtext DEFAULT NULL,
  `is_published` int(11) DEFAULT 0,
  `created_at` varchar(50) DEFAULT NULL,
  `updated_at` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_kegiatan_form_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `tugas_form` (
  `id` int(11) NOT NULL,
  `judul` varchar(255) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `keterangan` text DEFAULT NULL,
  `start_date` varchar(50) NOT NULL,
  `end_date` varchar(50) NOT NULL,
  `sunday_times` varchar(255) DEFAULT '08:00,10:00,17:00,19:00',
  `weekday_time` varchar(50) DEFAULT '18:00',
  `status` varchar(50) DEFAULT 'draft',
  `created_at` varchar(50) DEFAULT NULL,
  `published_at` varchar(50) DEFAULT NULL,
  `expires_at` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_tugas_form_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `tugas_form_slot` (
  `id` int(11) NOT NULL,
  `form_id` int(11) NOT NULL,
  `date` varchar(50) NOT NULL,
  `time` varchar(50) NOT NULL,
  `operator_username` varchar(150) DEFAULT NULL,
  `kameramen_username` varchar(150) DEFAULT NULL,
  `supervisor_username` varchar(150) DEFAULT NULL,
  `updated_at` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_tugas_form_slot` (`form_id`,`date`,`time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `tugas_form_audit` (
  `id` int(11) NOT NULL,
  `form_id` int(11) NOT NULL,
  `slot_id` int(11) NOT NULL,
  `actor_username` varchar(150) DEFAULT NULL,
  `actor_role` varchar(50) DEFAULT NULL,
  `actor_ip` varchar(50) DEFAULT NULL,
  `actor_route` varchar(255) DEFAULT NULL,
  `old_operator` varchar(150) DEFAULT NULL,
  `old_kameramen` varchar(150) DEFAULT NULL,
  `old_supervisor` varchar(150) DEFAULT NULL,
  `new_operator` varchar(150) DEFAULT NULL,
  `new_kameramen` varchar(150) DEFAULT NULL,
  `new_supervisor` varchar(150) DEFAULT NULL,
  `note` text DEFAULT NULL,
  `created_at` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
