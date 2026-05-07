-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 07 Bulan Mei 2026 pada 13.24
-- Versi server: 10.4.32-MariaDB
-- Versi PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `crembo_db_new`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `streaming_weekly_config`
--

CREATE TABLE `streaming_weekly_config` (
  `id` int(11) NOT NULL,
  `day_name` varchar(20) NOT NULL,
  `start_time` time NOT NULL,
  `mass_name` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `streaming_weekly_config`
--

INSERT INTO `streaming_weekly_config` (`id`, `day_name`, `start_time`, `mass_name`) VALUES
(47, 'Jumat', '18:00:00', 'Misa Harian'),
(48, 'Kamis', '18:00:00', 'Misa Harian'),
(49, 'Minggu', '10:00:00', 'Misa Mingguan'),
(50, 'Minggu', '16:30:00', 'Misa Mingguan'),
(51, 'Minggu', '18:30:00', 'Misa Mingguan'),
(52, 'Minggu', '07:30:00', 'Misa Mingguan'),
(53, 'Rabu', '18:00:00', 'Misa Harian'),
(54, 'Sabtu', '18:00:00', 'Misa Mingguan'),
(55, 'Selasa', '18:00:00', 'Misa Harian'),
(56, 'Senin', '18:00:00', 'Misa Harian');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `streaming_weekly_config`
--
ALTER TABLE `streaming_weekly_config`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `streaming_weekly_config`
--
ALTER TABLE `streaming_weekly_config`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=57;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
