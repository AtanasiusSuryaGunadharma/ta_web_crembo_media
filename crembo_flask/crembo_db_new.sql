-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 01 Bulan Mei 2026 pada 07.04
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
-- Struktur dari tabel `anggota`
--

CREATE TABLE `anggota` (
  `id` int(11) NOT NULL,
  `nama` varchar(255) DEFAULT NULL,
  `username` varchar(150) DEFAULT NULL,
  `telp` varchar(50) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(50) DEFAULT NULL,
  `tgl_lahir` varchar(50) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `alamat` text DEFAULT NULL,
  `status_akun` varchar(20) NOT NULL DEFAULT 'aktif',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `anggota`
--

INSERT INTO `anggota` (`id`, `nama`, `username`, `telp`, `password`, `role`, `tgl_lahir`, `email`, `alamat`, `status_akun`, `created_at`, `updated_at`) VALUES
(1, 'FX Harso Susanto', 'Babe', '085772732906', 'scrypt:32768:8:1$JyBWrrkOGuhe7jTd$54a802bcc99d80b72fd817a2e48f375e5ca0b60c4b17b9122e94bf8dbfeae146e509440f31c3a14e9ad60ba48f92b985f6ecc43b2f47a4b62af5cb3cf23fca08', 'admin', '1970-08-20', 'suksisnarf@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(2, 'Nico Gandawijaya', 'Niko', '082134997990', 'scrypt:32768:8:1$ko6WHg49UtiRs2dG$f5679cc0164f379e1eb6fd61be4e43dc6303bc9b4019893422296fd3c0737e82eab49f24542a03c982804f00299f9b9378e524cece687f91c3e93fe0948dce6b', 'admin', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(3, 'Christoforus Tadeus', 'Christoforus Tadeus', '085894525162', 'scrypt:32768:8:1$fSixa3Z12Exd4P0g$77ceac2f30d86b53d3149988a50272238460b0d29b5648b567fb8571ca8fe811d55ffadb3739dc2ffdc1379439f43f0ab34181ababb6698f465fd9a12332f4ec', 'admin', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(4, 'Riean Aditya', 'rieanaditya', '0895336757747', 'scrypt:32768:8:1$8FnTsAy3hjS6C622$32131dc844eb221136fa21134940d2b2452cf1e1e65af209404300ad95c71bb339b4fadb5e902e9b99fbf0304e652c9c50cc64b98d4e461ff28399f4d6ebdb40', 'admin', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(5, 'Katherine Ivana Hadi', 'Ketrin', '081386618220', 'scrypt:32768:8:1$kocjdDopnrgca8lt$83958b6ec208ca1facc17f762955dcd7f8285181930e43c16ceb506e11e9f1c0c957e7b0f7c3960a4f88b04ac5916e3cc16d9473455ffba02b9bf927cf9f89a4', 'admin', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(6, 'Pria', 'Pria', '081228330226', 'scrypt:32768:8:1$4nCgWeSwWR7cEYj3$d40e423b6ec59c153bfc0843476c48bcbffdcfe69844e4a9e942320107b0c624c3a68c1cb0a597bdbba85a117cbfbd0b3be743cb18abb77365a621a6f63c7eee', 'admin', '2026-04-29', 'pria@gmail.com', 'Jl Baciro', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(7, 'Aurel', 'Aurel', '085878495255', 'scrypt:32768:8:1$WsEELS5C525TKDKr$d70c89e1f0e8c98944a9b9a56e4927f19805d4ed92a319da6f7e6743884392281825a9298587241f07fc4af871e6013771f9a07471d79bff4df7ede78c44b0bd', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(8, 'Dewi', 'Dewi', '087700652865', 'scrypt:32768:8:1$z8mtUa3kB43bDHfP$5f8d2ff4647348ed2fc60b4eeaa8e027c892a1e2500cf4015554a2940367dbfa0d48a9d3c5b121e2ea6472abbdd2ea5e073e0bd7bcfe58b9e1ec62032813e80d', 'admin', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(9, 'Febrian', 'Febrian', '081220239158', 'scrypt:32768:8:1$v7BBX2N2uKgzq8gu$245b6a3723e1ddd0d0b3178c685448a8d792bd42d7ebd52d4ba423cfb89a5c9a85612c260f5f396a4e1a0b3cd4901605c6e06537a4f5622d83fb3fccd24f6e4a', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(10, 'Lisa', 'Lisa', '081327428922', 'scrypt:32768:8:1$zugzoG5d10AkzMMw$e01ff24899ee0f31c5aed313b7dce55a82d8888eee6144a6c42087df37cf413053eadd69a80cf63af2a6cce7fd4a154450c13c95eb7785029519285b3f467b93', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(11, 'Rosel', 'Rosel', '081919811671', 'scrypt:32768:8:1$O1LLlNyMX3bRjTBo$0029c8759982f8bcbb82dcfa08f7011c6683bc2dc6bae201959d90d8eb480131023d34cd9c022ecfb497b20a0b8ca63ba44e47641d08633bfcc66f10a18f4221', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(12, 'Vio', 'Vio', '085866168513', 'scrypt:32768:8:1$MQB3DJzR55lAxfRz$4e1c6da0f56406b6ff7fd39004e2a0e72a61d12e990ad4bb03aa6b47e74d3ec16e71eaf69541ee638d8d53079db24544ae5da0762b8545b0a92bdfc95ee84aef', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(13, 'Vista', 'Vista', '085876328357', 'scrypt:32768:8:1$VhoXIsf5sBBRQnej$91cab4e2d24456956e6c5dd96d0856b91c364c019fae6538f81f6477292350f7c63c9f7f393f40fe639bf379f0ca8624837b8ebf5add04050c4f2d07dd2495b4', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(14, 'Weka', 'Weka', '081327129511', 'scrypt:32768:8:1$X9L6HCXHYkOsnz7A$e10cad76e595424543b19ef0129860197d76c593ea713839805b46e03027e25e7f80bf50d3cb2c5245209f9ebbd0d3eea8a9c141e82161f50557413c8e3bf0ac', 'admin', '2009-09-09', 'wekawijaya044@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(15, 'Wima', 'Wima', '089508852626', 'scrypt:32768:8:1$DkrEKgzzK58KDWRJ$22c21297aadeaf6c23a71851f6f0b1fdceafc3cab46c3f64efc135d3f057835eb22c33aaf01793e649cc71d444436edd32676cc1c8da5699894fd03e6c3a2bd4', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(16, 'Nawung', 'Nawung', '081228680603', 'scrypt:32768:8:1$8eC2MkZma35ywHMU$883da4c68fb22452c790379a3d27d3213c8d08bd0984dbe900ecc0d843f7a8c50ec342c0bb29e56d82ae537c267b82c071cd4bd7f702798845d88133d7644cf9', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(17, 'Panji', 'Panji', '089677330106', 'scrypt:32768:8:1$E62Rv9BJW0qyjSdV$a15df746db84de526237ed4597d310d6aecec556024877a2ef0bfcf847a45ec4e9942ae4abda89e3c56aa0469721393cfabfb4a37dce0d98b403dc1020869934', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(18, 'Yuta', 'Yuta', '085602917625', 'scrypt:32768:8:1$aRKL0gXhh4swWOYH$17feeca47d7286fb51d169dda8f755eb6e42145bb184deaeae0ed314cb14fd83edaeb675c71ec7ba506f7b68954ed85aa5eebbad32fefabdb6bcde3a32b278b6', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(19, 'Shehan', 'Shehan', '087878836187', 'scrypt:32768:8:1$oyUllzXRah1PHjZ8$266f06fb807d46674aba4a1d54733bdd385971eac547a54bb518f206dc98bcd32b59670a59019467fdf912cab1ccf4f85c05177d84ee3ed83dbf197e4d2838a9', 'admin', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(20, 'Asha', 'Asha', '081226402137', 'scrypt:32768:8:1$fEMSfKPrYGs77Bf5$6c4bf03bafdf6a39cdf6ec3a58f0715ea71714fcfb97bc464d5beb45a078e40d5a5a7eed6294a760af4b1a63de52d67319501ba3ecca44a4e5ca24827f0c9d51', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(21, 'Aura', 'Aura', '088215905899', 'scrypt:32768:8:1$8RCaZofpMtIEDQVP$1f5bdac57f12d3c4d49c8db23148b3145da7cca697173c796a2d342174b9da9f275207ce6fedff60f8c8dac3ffe0a6ac63c4ed88cc08f7a2d1e9327416ee3e1e', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(22, 'Belinda', 'Belinda', '083146801642', 'scrypt:32768:8:1$9qd2Zy3VegtCGFHn$d14fafb239f6f3e8bf0dd862471ad6b2e3070af2abbd67c2439498bbff64ad003e894fc1e7cf5f475273c379aa8f8fd2d5dfb0ff13b2ae7c1f8d695ef4babe9f', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(23, 'Bian', 'Bian', '089694800055', 'scrypt:32768:8:1$spGXHMjT3MUWjBH7$4ff3d50e25265020283510214ef615c8eb56d557c37f372eb2d52e01adf26b900f3d8b9c4c050139945f812e3bff6dc6dd6a5953ae6924031fccf390e1c460c0', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(24, 'Bima', 'Bima', '0818112847', 'scrypt:32768:8:1$ixgFvPKkDANWB4SG$718405ff79ae853f5c6ed7b42084621ce7b292b40c095b44a78e6ece1a4e83abed472fb9c046b9328f3dd3fe7c0b3b1f7c452b8f9514ddf03b598f0186019aef', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(25, 'Botun', 'Botun', '081378591744', 'scrypt:32768:8:1$y8nOtt5q4HXUWnrP$f2a763bb9640d9a69405a0cf52c9b1814520f404cd62acb7568e4d0a60c6bd7d153f803278d2326e95e1d0e14df82152ecd2a270ab984e07976784ad29c28f4c', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(26, 'Claire', 'Claire', '082224063848', 'scrypt:32768:8:1$WJhJwJZ8lwOVke4o$e47392ac968708a21ab949c555cd2bb6ebede6468e27bc1e17313a2c5ae1488a7072a0882c06a0436e1ee162d82d77c1059d4879444fde6863f536815ee18ebd', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(27, 'Florencia', 'Florencia', '081329017910', 'scrypt:32768:8:1$qksHCQRkvMPAO9h1$0437f83eb6de474ffc8ca4d6056137ee20a281c4774424b71da9c9e824ba93041792c010e3473152b7881823f9e06788aa3a7f0c5763032e092416d5d6054b8e', 'user', '2010-07-07', 'vlflorencialidya@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(28, 'Ifa', 'Ifa', '0882007217238', 'scrypt:32768:8:1$LnEWLueSEc2uz3Bt$15cb6dff047fa026f131bf92b79539aacf01707f07c401b2ff355053ccd2f7705faa32d6dd80eb9f8775a51743af126bc2dd11100250d143117800eedc579e46', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(29, 'Jeni', 'Jeni', '085248994747', 'scrypt:32768:8:1$dies2yefonWdDRJm$055401c9134ca88d2d1191c02f0e91a6dafdd9b2564957ad1c6842b954e3e018791b04826a8794aae0155e6b4b9f46cf2a73d4332a534bfeecb4d28d2da8d2b5', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(30, 'Jossefina', 'Jose', '0895321245610', 'scrypt:32768:8:1$TnitTZEy6j78SsFn$cea859177bafa0ec3e2499c60729dc5ad9fe6b18ef0155c8eadc13cf75822c2b09fbcc0d57b79c5c028ad0a97029440398d1feab7b5182fdb7ba66ea3cbf7f60', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(31, 'Kanes', 'Kanes', '089675333345', 'scrypt:32768:8:1$jzhfgo7Sr1Lueftt$675a2469c4a4636c037565cb8b18b4586f88a98a81fefe979ff2e2ac27a57f3fb80af2b5a3b1024b5b8db0447f4961214fcf3604d3c39322a95283ef2ce826ab', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(32, 'Kinan', 'Kinan', '081239902121', 'scrypt:32768:8:1$MiUAKrxwhsdO5gES$4736c7dbc71b0ed9acfb6cc1a45403afd6a3b31cd6e6e64909f4e525708be15b2c0edc3bf98197aae393b4c6f28c1b2eb1a3423a43e24b4d86f4341078acd9e8', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(33, 'Veny', 'Veny', '082271499065', 'scrypt:32768:8:1$HTAwll6LRFjM3Jlo$a2f7cfde57033414d36b38fcbce69516dcad40ae02bc4e84d1367e877d9856c145210dcbf1af83733c77f2ad827f2327ac5cf045f65adb20bbd0adf1007c17a0', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(34, 'Juven', 'Juven', '082247972976', 'scrypt:32768:8:1$hQ1x54n6LWot5VYV$a2ba1bf9b1c6babdf603fb99addb241900fd5604b314ee7c1c9751446da06b715d8cdf6d44671db9c8740dae9a52ba7ac3e47ab9a2cf14057cd0dd3d5ec77d0e', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(35, 'Chris', 'Chris', '081213430315', 'scrypt:32768:8:1$R1dD1KBC9u9PKfNy$701279e4f400341c73b34290165e86e8879fbfb4a4daa9d59ccd734a84c7bbd80e5fed1f02ed18d0a4334ad46ab2b32dd56f7a3826d42087eff4a7828801e788', 'user', '2026-04-29', 'chris@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(36, 'Alta', 'Alta', '081229910550', 'scrypt:32768:8:1$z99rBAe6O6BmRrCg$ba572b8ef08c050dbcb7032417b2740f8ebb29efa76c91cada77c5cc225dfc65641d9cd4b57982a5fe0742d9daff02dd31875d51f7e336afdb1509dc4a65aab2', 'user', '2026-04-29', 'alta@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(37, 'Rikha', 'Rikha', '081254106511', 'scrypt:32768:8:1$qQh5HoIuf3oqRplz$5c332edd766cbed1b458d0d71f611c850d0a809d3ee5722af4183226a26141dc755eca74ca87b5e88d54fd27b9f14abc04d67d92e5d63ae6e2cd515e584d55cf', 'user', '2026-04-29', 'rikha@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(38, 'Michell', 'Michel', '081772854812', 'scrypt:32768:8:1$ZYiCgWAD2KeMwFGq$ec99d80b98d65745df18255daedc79b4a4402e4285ff850549c8eba0cddf5f5096835bc882c127f55b9c91788c4c9b6d92875b050b07c17e21ea8819b2cfc632', 'user', '2026-04-29', 'michel@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(39, 'Michelle', 'Michelle', '083838025077', 'scrypt:32768:8:1$S7szxLHJBy7K7bLi$bd8bc8dbc11217c65eea78ded7c9912fb2f22801963bb5c20dc3a01a606f9c5c0c7c2c542dc06fa6873550af41fc882815e74dba5904a1f77d8ade5d80ac1fb0', 'user', '2026-04-29', 'michelee@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(40, 'Naresh', 'Naresh', '085879271256', 'scrypt:32768:8:1$DQMapYNxMGqcRtHa$8143d5aca1985488b61a218bf23fdef3c267f10a714f012d6457f42d375aeef02fbd89f351c1925cf791cf0b00b47332d43dbd61837d2b1aabe6509943b7a237', 'user', '2026-04-29', 'naresh@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(41, 'Nesto', 'Nesto', '082122760357', 'scrypt:32768:8:1$HvsT0YViHYwCn8Tn$00674242159227cf6dce2295513d9b74597154cd84f49498472029693112499dc2de14f2483761a05215d1ada40bbf8f8fb2303d0f92aa6483bd1854403c685b', 'user', '2026-04-29', 'nesto@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(42, 'Noel', 'Noel', '081568261411', 'scrypt:32768:8:1$EIx5tRRMYa5ng11G$f8ba9a40a7fd536d48b95eeece57b5d47c7b2c23a9e0cf1b1b3336a1cbaf85640b140ff5c2e6e13732bf23c51efde894c881325ab25f95836bfdb74070becde7', 'user', '2026-04-29', 'noel@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(43, 'Paul', 'Paul', '088802686783', 'scrypt:32768:8:1$Yt2s6jWtsIww9QPC$74ed569487811366d290d02dedca99637f9dfec228d1170febc9a7ffe5144e1e4277a87025a784cc4b7d568428577b5dd3dad683df7246c8539b7f9f546e9a92', 'user', '2026-04-29', 'paul@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(44, 'Putra', 'Putra', '082243122313', 'scrypt:32768:8:1$RZFbloXwMMISgV5n$ffa25bee6f54a2f21d878e1a130af64a1a2595e65cb6e332af293498bc805bb40aa637f96b479b1448d8d101a97d6bba8e42e4d4095d4b44f53f6730cf63d354', 'user', '2026-04-29', 'putra@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(45, 'Rossa', 'Rossa', '08895799655', 'scrypt:32768:8:1$eE7CHjhWnzrPs9Ww$27447c8f095aa919adb7a362197c2af08fcb253a425625c83864ea393d4e6a5250b071e98f69b1c008742f0a2e30038e797b5b8e62c8b3c24999f9a7c5750541', 'user', '2026-04-29', 'rossa@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(46, 'Satrio', 'Satrio', '088806790315', 'scrypt:32768:8:1$XUE0q9zEL1gk1ytu$a0507f02d9c35223190dc17f018128fafd8ac6b94efb03cdb5377ed0e65d5f9608cd42f60de86855b01908476f1a0be82d68b2129cd33ec0f1a67b3609482b54', 'user', '2026-04-29', 'satrio@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(47, 'There', 'There', '087898555370', 'scrypt:32768:8:1$IURMpb4BKozcqzQv$723f337692d6b0d53fb92fe0fe09155c782e20fd28efdde82b965db14ec9bc78672524ea4a751f681dd839f960a1e26a671051c4f37c31eea9338d5261bc7ef8', 'user', '2011-01-30', 'yoshefasabatini@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(48, 'Toto', 'Toto', '085820134705', 'scrypt:32768:8:1$YJlFgQbsb2jXCukn$9d06995e524e5bd8a46383d786634a3a95974229cdaece7ac41411f3489dbec4185e71040493b5c072a7262d2bc724bfa781a8f5861f358ea29ba525b1b9b67d', 'user', '2026-04-29', 'toto@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(49, 'Tyas', 'Tyas', '088985826095', 'scrypt:32768:8:1$rbhGaMjTfmgzPkVY$6fa412ca61b11f8cb4530b5b25a32cf75e5770e99f0b741405a33ae139fbaa3414d9c9155f987bde4461cd3568f886fecdee0f02c4436e4b8ebaea7958304183', 'user', '2026-04-29', 'tyas@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(50, 'Atanasius Surya', 'Ata Surya', '081350751753', 'scrypt:32768:8:1$kFm1YQAwwqqqQfaj$f8572ecea4f1f036820af1875cde3e5984bf830f363914c892844527c04502a3f17b4889d9ef2e121228a35bba1a674cc20e5a6d81c497e27092bd310ab9ae65', 'super_admin', '2004-05-13', 'atanasiussurya@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:59:05'),
(51, 'Rafael', 'Rafael', '081390333758', 'scrypt:32768:8:1$XTjB22QBETTUwjPH$2a4f5f9da5660c3b8f94f928ea8e76ddebf18f576c1f36a5c526c01dd032081466edf3f2cb14ad766d1dc3820f5f763d18ae13d63bdae711d422759b31339168', 'user', '2026-04-29', 'rafael@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(52, 'Frugal', 'Frugal', '081398307591', 'scrypt:32768:8:1$D03o2WrlrPCX74Bo$72cdb406fc98e86d38df12ce1c8a48663dc428ef7bb713c088fd8bf266b87db957219d003b0f939d6c82dfe5f7d6d3bf652a0a591caf0352b323a636e5505c7b', 'user', '2026-04-29', 'frugal@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(53, 'Daflo', 'Daflo', '082157663661', 'scrypt:32768:8:1$qYu1t0PYcrvx7Ub6$4537820f12b8e4e212f818059949df3b7827aa82ce621327c48f49e0eda76aac09876c6a6ef8ad18d66df1dc31cf24fdaf3f38235e80501b173330c5c5709e70', 'user', '2026-04-29', 'daflo@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(54, 'Orel', 'Orel', '083865646354', 'scrypt:32768:8:1$qs2s3KqRqZw1eETw$c9fcfd8727fe0cbfe0424bad9a58c4d5fc9e881d9152e37a39ba68d554468d566760eeb272b6c561419881f8e10fdf97b3370138fd5bb0fb06924a0389e13aaa', 'user', '2026-04-29', 'orel@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(55, 'Jeje', 'Jeje', '085171503299', 'scrypt:32768:8:1$vdKYr7PknsBZp06Q$c4f882227a43d10bb74b4e0b8add4d85cdc28b5f0272c701ac55ff48accb0f56c9fbb1a826c9e4cd3788585e2e896485617861a1dcf920749389ef54f8edb2cc', 'user', '2026-04-29', 'jeje@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(56, 'Regio', 'Regio', '087877555879', 'scrypt:32768:8:1$nRWs4w7Hr0NeJanf$45cde6f342a36b065dbf5034882dd19e2d126fcec974ee093619ce7b02b67305fa341c390dc71deadc933744e239a75931956cd60be37d7c63923f73cbec511f', 'user', '2002-11-29', 'regionanda2@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(57, 'Nadia', 'Nadia', '085797307843', 'scrypt:32768:8:1$5Y1pVLD71ql68qoU$2b7cb6ac920cb2ad2f5c82cbe7ed1ba32a23aedac03b273571ce4eca8930fd0643860920da68edc27ad7cc8b8b33044e6e7c111aae1f9d345af8876a9e9ba40d', 'user', '2026-04-29', 'nadia@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(58, 'Tita', 'Tita', '085624236122', 'scrypt:32768:8:1$ThJvle16qAEZEXe9$4fcd81d7ab981e7c040c1df112ec5c51418f8c75ae13d3f3cee9c9b276f1d790eb993aad5dd70177f55f20e1ea9eb0f27cbea5feec48993c1e9f96278de0b612', 'user', '2026-04-29', 'tita@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(59, 'Floren', 'Floren', '082146937640', 'scrypt:32768:8:1$b03ee1H4ci0zSrVO$0c988d0ab6e82d2d8c1e60ba3c3cfa2919d44f6de8c135af5539ba6c92cd1366ae0b27a945a2f02d1a6a9881b2292bda319f5e4f902ff1ddcb324e9a2e3b5953', 'user', '2005-06-20', 'flojuni236@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(60, 'Baladeva', 'Deva', '082286767108', 'scrypt:32768:8:1$96QCeigF8xsu8IZF$8d248c68043ea3b902c3c3b4821e0e6273328d60e94ede7c21bf45aeccf53f0e432dbb5c73eb6d09cc420048f329ea35ba83b031760eab09fe451c71afc68f6b', 'user', '', 'anggota@example.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(61, 'Chessa', 'Chessa', '087883075397', 'scrypt:32768:8:1$ufUyCIhP6VEoLqtH$228d0ba6caa4e5cc15f633c1d697935a930bfb035a55f303522f0711ed980d06e052ecd64715d21ed171fd8f92b90975dca4a91ec9bb4f741aa36793634fed0e', 'user', '2026-04-29', 'krin3112@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(65, 'Dhani', 'Dhani', '085868202008', 'scrypt:32768:8:1$c80fb04psPvyRhwK$ba5f9452efd6714223668efe346b886234747efbdadda641f89c6043ef7787693536bb397aed2d9ded0eeb7e85b79c59aec23c9c47291f60ff4924a7cab956cb', 'user', '', 'ardhani.ign@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(66, 'Evan', 'Evan', '088239466566', 'scrypt:32768:8:1$rA0YHXLWixjOuBWo$e56e9267f006c0507aa23eafa0c29cabfcfbe53496316b2708b8aaa0d4b546ce3feb3f03fa3c9db6270a541ef9f8eae8d6096e2f1771c8333cb92423add6e127', 'user', '', 'evanpaskalis464@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(67, 'Aruna', 'Aruna', '081973372901', 'scrypt:32768:8:1$vW6eHF8B4YJ6MbFs$c38dbfd05be7673a5064fe2c6799e2363b2b62ae6cf3c515b853ff2214f61854dfd4d6f0b7bfde77b7ba4a1c5b96e70cdb110562933a2f178378e70e5d67878d', 'user', '', 'arunayudyaw@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(68, 'Egi', 'Egi', '087715815710', 'scrypt:32768:8:1$gMectZBAUXWHfN8J$37faf85dc311c2403705d21c74e4870a1b326596644421d61c2b76513e05e8516bc59841b4afb99b6fa20de33d808419f95449c932f965e1b519dca67a66a31d', 'user', '', 'regina.caelia18@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(69, 'Reva', 'Reva', '082325249481', 'scrypt:32768:8:1$Nyn6g6Orn3h2grlg$f2de22fcf0501ffe227e9e14b8c5496d2a94625e0674f000207c05468db3c17a8e43f9a9894e744c87b63c58280b096b9040b7f0afb05115fa1d8710bd512a3b', 'user', '', 'lrevadewi@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(70, 'Kane', 'Kane', '081919090631', 'scrypt:32768:8:1$dz0dJJxmAWSdkSia$fc492396568f1962d6455f0d19e92b53b224045af923a4fecb892447516425f8551343c92ce4f991f65fac0a34a331b31d56135dea9f1f7eae471bea3c135608', 'user', '', 'regina.kns17@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(71, 'Stella', 'Stella', '089613983033', 'scrypt:32768:8:1$bXDQCOaFeT7rh4iN$771d95d2caf7280673b7e3e6fdeada15d35bc16986ab59ad5fad3a9a2c5b53f9ef9f0f9a6e7844f2bfda029d87f40bdeafc5174a8a45e4a4514415b14bedcb69', 'user', '', 'stellamaria758@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(72, 'Arya', 'Arya', '081324859094', 'scrypt:32768:8:1$i611QYvOcmtTNXBt$8f443083de045a9d389a51e27a4ca5713296679e91c2203e870245b56d60ab016d1063f8587a14004cfc1cd9ce7e7cc323827bcb7c1300c9ea86a1e05d74a309', 'user', '', 'aryadwika2010@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(73, 'Aoki', 'Aoki', '085743665416', 'scrypt:32768:8:1$uVLwUhPRoRMREi5O$401e7e9b5f793f89952b3845f87ebec60e64faff8655f816ef82541465a7a0e2b82b02aa00602ec61f6a75c939d2e528d671547a507b46c4f4b0629c752103b5', 'user', '', 'gizelleraina2401@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(74, 'Luciana Tyas', 'Luciana Tyas', '0895630325989', 'scrypt:32768:8:1$G8tPh3OwDuLnwYYe$b75e000738a948ec413c8d092d2761b6cf1ba990c2f38b3686ecfb16b875dd5ba510348cab7f763fddbce1fdae2863829ad267dffc94d42c6aab89d15625f174', 'user', '', 'lucianaxaverinetyas@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14'),
(75, 'Callista', 'Callista', '087836461101', 'scrypt:32768:8:1$Tx9b068Kbha1DNhD$7ed5c89ddd38db5955dc7d40ac96539c974f0197189167725b0f96828fb3d97437c1cd41981f42bc04b1636419e567f6f7f634695e7b2de25afc032ff6b98a96', 'user', '', 'lumodocalista@gmail.com', 'Alamat belum diisi', 'aktif', '2026-04-30 01:16:14', '2026-04-30 01:16:14');

-- --------------------------------------------------------

--
-- Struktur dari tabel `carousel_slides`
--

CREATE TABLE `carousel_slides` (
  `id` varchar(100) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `slug` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `button_text` varchar(100) DEFAULT NULL,
  `button_link` varchar(255) DEFAULT NULL,
  `background_image` text DEFAULT NULL,
  `order_index` int(11) DEFAULT 0,
  `is_visible` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `carousel_slides`
--

INSERT INTO `carousel_slides` (`id`, `title`, `slug`, `description`, `button_text`, `button_link`, `background_image`, `order_index`, `is_visible`) VALUES
('slide-1777501533719', 'Tes Slide 1', 'tes-slide-1', 'Tes Slide 1', 'Lihat Detail', 'https://www.ampta.ac.id/', 'uploads/foto_baju_koki_1777501490.jpg', 1, 1),
('slide-1777501608227', 'Tes Slide 2', 'tes-slide-2', 'Tes Slide 2', 'Lihat Detail', 'https://jurnal.ampta.ac.id/', 'uploads/screencapture-regresiipkapp-hri4gibhumniyaspcxyehz-streamlit-app-2026-04-16-21_14_39_1777501565.png', 2, 1),
('slide-1777501680625', 'Tes Slide 3', 'tes-slide-3', 'tes slide 3', 'Lihat Detail', 'https://pascasarjana.ampta.ac.id/', 'uploads/User_Journey_Map_User_Biasa_1777504646.png', 3, 1);

-- --------------------------------------------------------

--
-- Struktur dari tabel `google_maps_embed`
--

CREATE TABLE `google_maps_embed` (
  `id` int(11) NOT NULL,
  `url` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `google_maps_embed`
--

INSERT INTO `google_maps_embed` (`id`, `url`) VALUES
(1, 'https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d14308.98777372105!2d110.389635!3d-7.791248!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e7a59d773957dad%3A0xae048b4c2addab14!2sGereja%20Katolik%20Paroki%20Kristus%20Raja%2C%20Baciro!5e1!3m2!1sid!2sid!4v1777498907792!5m2!1sid!2sid');

-- --------------------------------------------------------

--
-- Struktur dari tabel `instagram_posts`
--

CREATE TABLE `instagram_posts` (
  `id_instagram` varchar(100) NOT NULL,
  `judul_instagram` varchar(200) NOT NULL,
  `url_instagram` varchar(255) NOT NULL,
  `urutan` int(11) NOT NULL DEFAULT 0,
  `tgl_instagram` datetime DEFAULT current_timestamp(),
  `ip` varchar(25) DEFAULT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `instagram_posts`
--

INSERT INTO `instagram_posts` (`id_instagram`, `judul_instagram`, `url_instagram`, `urutan`, `tgl_instagram`, `ip`, `status`) VALUES
('ig-1777491045898', 'Oprec Crembo 2025', 'https://www.instagram.com/p/DLM-_zlzR2Q/?utm_source=ig_web_button_share_sheet&igsh=MzRlODBiNWFlZA==', 1, '2026-04-30 02:56:49', '127.0.0.1', 1),
('ig-1777491111872', 'Tipe-tipe petugas Crembo waktu Misa', 'https://www.instagram.com/reel/DWszMKVDd4H/?utm_source=ig_web_button_share_sheet&igsh=MzRlODBiNWFlZA==', 2, '2026-04-30 02:56:49', '127.0.0.1', 1),
('ig-1777491154924', 'Dokum Tablo 2025', 'https://www.instagram.com/p/DIwR16YSqQf/?utm_source=ig_web_button_share_sheet&igsh=MzRlODBiNWFlZA==', 3, '2026-04-30 02:56:49', '127.0.0.1', 1),
('ig-1777492609498', 'Iklan EKM', 'https://www.instagram.com/p/DN2a-xE5p0C/?utm_source=ig_web_button_share_sheet&igsh=MzRlODBiNWFlZA==', 4, '2026-04-30 02:56:49', '127.0.0.1', 1);

-- --------------------------------------------------------

--
-- Struktur dari tabel `kegiatan`
--

CREATE TABLE `kegiatan` (
  `id` int(11) NOT NULL,
  `judul` varchar(255) NOT NULL,
  `tanggal` varchar(50) NOT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'draft',
  `misa_json` longtext NOT NULL,
  `created_at` varchar(50) NOT NULL,
  `updated_at` varchar(50) NOT NULL,
  `misa_ke` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `kegiatan`
--

INSERT INTO `kegiatan` (`id`, `judul`, `tanggal`, `status`, `misa_json`, `created_at`, `updated_at`, `misa_ke`) VALUES
(1, 'Misa Rabu Abu', '2026-02-18', 'deleted', '[]', '2026-01-24 10:03:33', '2026-01-25 22:18:20', NULL),
(2, 'Misa Rabu Abu', '2026-02-18', 'deleted', '[]', '2026-01-24 10:46:01', '2026-01-25 22:18:28', NULL),
(3, 'Misa Rabu Abu', '2026-02-18', 'deleted', '[{\"misa_ke\": 1, \"jam\": \"17:00\", \"dp_username\": \"Daflo\", \"op_username\": \"Christoforus Tadeus\", \"vmix_username\": \"Claire\", \"kamera\": [\"Chris\", \"Chessa\", \"Callista\"], \"supervisor\": [\"Botun\", \"Bima\", \"Bian\"], \"fotografer\": [\"Belinda\", \"Babe\", \"Aurel\"]}, {\"misa_ke\": 2, \"jam\": \"19:01\", \"dp_username\": \"Daflo\", \"op_username\": \"Claire\", \"vmix_username\": \"Christoforus Tadeus\", \"kamera\": [\"Chris\", \"Chessa\", \"Callista\", \"Aurel\"], \"supervisor\": [\"Botun\", \"Bima\", \"Bian\"], \"fotografer\": [\"Belinda\", \"Babe\"]}]', '2026-01-25 02:01:08', '2026-01-25 22:18:05', NULL),
(4, 'Misa Rabu Abu', '2026-02-17', 'deleted', '[{\"misa_ke\": 1, \"jam\": \"18:00\", \"dp_username\": \"Vio\", \"op_username\": \"Vio\", \"vmix_username\": \"\", \"kamera\": [\"Wima\", \"Orel\", \"Lisa\"], \"supervisor\": [\"There\", \"Callista\"], \"fotografer\": [\"Stella\", \"Ketrin\"]}]', '2026-01-25 21:10:54', '2026-01-25 22:18:15', NULL),
(5, 'Misa Rabu Abu', '2026-02-17', 'publish', '[{\"misa_ke\": 1, \"jam\": \"18:00\", \"dp_username\": \"Vio\", \"op_username\": \"Lisa\", \"vmix_username\": \"\", \"kamera\": [\"Wima\", \"Orel\", \"Dhani\"], \"supervisor\": [\"There\", \"Callista\"], \"fotografer\": [\"Stella\", \"Ketrin\"]}]', '2026-01-25 22:46:53', '2026-01-31 12:50:45', NULL),
(6, 'Misa Rabu Abu', '2026-02-18', 'publish', '[{\"misa_ke\": 1, \"jam\": \"16:30\", \"dp_username\": \"Belinda\", \"op_username\": \"Christoforus Tadeus\", \"vmix_username\": \"\", \"kamera\": [\"Reva\", \"Luciana Tyas\", \"Asha\"], \"supervisor\": [\"Pria\", \"Jose\"], \"fotografer\": [\"Naresh\", \"Aruna\"]}, {\"misa_ke\": 2, \"jam\": \"18:30\", \"dp_username\": \"Aura\", \"op_username\": \"Ata Surya\", \"vmix_username\": \"\", \"kamera\": [\"Rikha\", \"Chessa\", \"Jeni\"], \"supervisor\": [\"Evan\", \"Panji\"], \"fotografer\": [\"Weka\", \"Egi\"]}]', '2026-01-25 22:52:51', '2026-01-31 12:47:44', NULL),
(7, 'Misa Minggu Palma', '2026-03-28', 'publish', '[{\"misa_ke\": 1, \"jam\": \"18:00\", \"dp_username\": \"Ata Surya\", \"op_username\": \"Aura\", \"vmix_username\": \"Regio\", \"kamera\": [\"Rikha\", \"Tita\", \"Rossa\", \"Jeni\"], \"supervisor\": [\"Claire\", \"Dhani\", \"Ifa\"], \"fotografer\": [\"Aurel\", \"Nawung\"]}]', '2026-02-22 17:56:38', '2026-02-25 18:26:03', NULL),
(8, 'Misa Minggu Palma', '2026-03-29', 'publish', '[{\"misa_ke\": 2, \"jam\": \"07:30\", \"dp_username\": \"Ketrin\", \"op_username\": \"Deva\", \"vmix_username\": \"Florencia\", \"kamera\": [\"Jeni\", \"Rikha\", \"Jose\", \"Callista\"], \"supervisor\": [\"Nadia\", \"Luciana Tyas\", \"Kanes\"], \"fotografer\": [\"Aoki\", \"Aruna\"]}, {\"misa_ke\": 3, \"jam\": \"10:00\", \"dp_username\": \"rieanaditya\", \"op_username\": \"Rafael\", \"vmix_username\": \"Wima\", \"kamera\": [\"Ata Surya\", \"Satrio\", \"Jeje\", \"Regio\"], \"supervisor\": [\"Pria\", \"Christoforus Tadeus\", \"Noel\", \"Dewi\"], \"fotografer\": [\"Paul\", \"Weka\"]}, {\"misa_ke\": 4, \"jam\": \"16:30\", \"dp_username\": \"Vio\", \"op_username\": \"Lisa\", \"vmix_username\": \"Aurel\", \"kamera\": [\"Reva\", \"Kane\", \"Arya\", \"Dhani\"], \"supervisor\": [\"Evan\", \"There\", \"Panji\"], \"fotografer\": [\"Belinda\", \"Bian\"]}, {\"misa_ke\": 5, \"jam\": \"18:30\", \"dp_username\": \"Wima\", \"op_username\": \"Orel\", \"vmix_username\": \"Asha\", \"kamera\": [\"Kanes\", \"Jose\", \"Aura\", \"Stella\"], \"supervisor\": [\"Tyas\", \"Regio\", \"Ata Surya\"], \"fotografer\": [\"Jeje\", \"Chessa\"]}]', '2026-02-22 17:59:19', '2026-03-04 16:16:34', NULL),
(9, 'Misa Kamis Putih', '2026-04-02', 'publish', '[{\"misa_ke\": 1, \"jam\": \"17:00\", \"dp_username\": \"Bian\", \"op_username\": \"Belinda\", \"vmix_username\": \"There\", \"kamera\": [\"Lisa\", \"Reva\", \"Vio\", \"Kane\"], \"supervisor\": [\"Panji\", \"Arya\", \"Evan\"], \"fotografer\": [\"Aurel\", \"Dhani\"]}, {\"misa_ke\": 2, \"jam\": \"19:30\", \"dp_username\": \"Christoforus Tadeus\", \"op_username\": \"Tita\", \"vmix_username\": \"Rossa\", \"kamera\": [\"Chessa\", \"Rikha\", \"Jeni\", \"Ifa\"], \"supervisor\": [\"Stella\", \"Arya\", \"Botun\"], \"fotografer\": [\"Claire\", \"Nawung\"]}]', '2026-02-22 18:12:11', '2026-02-25 18:25:47', NULL),
(10, 'Ibadat Jalan Salib Meditatif', '2026-04-03', 'publish', '[{\"misa_ke\": 1, \"jam\": \"09:00\", \"dp_username\": \"Shehan\", \"op_username\": \"Jeje\", \"vmix_username\": \"\", \"kamera\": [\"Nadia\", \"Lisa\"], \"supervisor\": [\"Pria\", \"Noel\"], \"fotografer\": [\"Ketrin\", \"Rafael\"]}]', '2026-02-22 18:14:17', '2026-03-04 15:16:23', NULL),
(11, 'Ibadat Jumat Agung', '2026-04-03', 'publish', '[{\"misa_ke\": 1, \"jam\": \"15:00\", \"dp_username\": \"Jeje\", \"op_username\": \"Ketrin\", \"vmix_username\": \"Deva\", \"kamera\": [\"Rafael\", \"Florencia\", \"Claire\", \"Callista\"], \"supervisor\": [\"Chessa\", \"Noel\", \"Nadia\"], \"fotografer\": [\"Regio\", \"Nawung\"]}, {\"misa_ke\": 2, \"jam\": \"18:30\", \"dp_username\": \"Orel\", \"op_username\": \"Asha\", \"vmix_username\": \"Wima\", \"kamera\": [\"Luciana Tyas\", \"Aruna\", \"Kanes\", \"Jose\"], \"supervisor\": [\"Tyas\", \"Naresh\", \"Noel\"], \"fotografer\": [\"Aura\", \"Stella\"]}]', '2026-02-22 18:18:00', '2026-03-12 18:57:33', NULL),
(12, 'Misa Malam Paskah', '2026-04-04', 'publish', '[{\"misa_ke\": 1, \"jam\": \"17:00\", \"dp_username\": \"Niko\", \"op_username\": \"Vio\", \"vmix_username\": \"Lisa\", \"kamera\": [\"Dhani\", \"Evan\", \"Bian\", \"Belinda\"], \"supervisor\": [\"Panji\", \"There\", \"Arya\"], \"fotografer\": [\"Weka\", \"Kane\"]}, {\"misa_ke\": 2, \"jam\": \"20:30\", \"dp_username\": \"Pria\", \"op_username\": \"Asha\", \"vmix_username\": \"Orel\", \"kamera\": [\"Wima\", \"Rafael\", \"Nadia\", \"Naresh\"], \"supervisor\": [\"Panji\", \"Egi\", \"Tyas\"], \"fotografer\": [\"Nawung\", \"Paul\"]}]', '2026-02-22 18:21:51', '2026-02-25 18:25:35', NULL),
(13, 'Misa Minggu Paskah', '2026-04-05', 'publish', '[{\"misa_ke\": 1, \"jam\": \"08:00\", \"dp_username\": \"Aura\", \"op_username\": \"Claire\", \"vmix_username\": \"Christoforus Tadeus\", \"kamera\": [\"Callista\", \"Kanes\", \"Chessa\", \"Botun\"], \"supervisor\": [\"Jose\", \"Aruna\", \"There\"], \"fotografer\": [\"Luciana Tyas\", \"Aoki\"]}, {\"misa_ke\": 2, \"jam\": \"18:00\", \"dp_username\": \"Deva\", \"op_username\": \"Florencia\", \"vmix_username\": \"Pria\", \"kamera\": [\"Tita\", \"Ifa\", \"Rossa\", \"Egi\"], \"supervisor\": [\"Botun\", \"Stella\", \"Naresh\"], \"fotografer\": [\"Tyas\", \"Satrio\"]}]', '2026-02-22 18:33:01', '2026-03-12 18:43:21', NULL),
(14, 'Ibadat Sabtu Suci', '2026-04-04', 'publish', '[{\"misa_ke\": 1, \"jam\": \"05:30\", \"dp_username\": \"Shehan\", \"op_username\": \"Weka\", \"vmix_username\": \"\", \"kamera\": [\"Dewi\", \"Christoforus Tadeus\"], \"supervisor\": [\"Tyas\"], \"fotografer\": [\"Paul\"]}]', '2026-03-04 15:17:21', '2026-03-14 20:57:32', NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `kegiatan_form`
--

CREATE TABLE `kegiatan_form` (
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
  `updated_at` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `news`
--

CREATE TABLE `news` (
  `id` varchar(100) NOT NULL,
  `title` varchar(500) NOT NULL,
  `slug` varchar(500) NOT NULL,
  `content` longtext NOT NULL,
  `summary` text DEFAULT NULL,
  `thumbnails` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`thumbnails`)),
  `attachments` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`attachments`)),
  `status` varchar(20) DEFAULT 'draft',
  `published_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `news`
--

INSERT INTO `news` (`id`, `title`, `slug`, `content`, `summary`, `thumbnails`, `attachments`, `status`, `published_at`, `created_at`, `updated_at`) VALUES
('news-1777593072897', 'Test Berita', 't', '<p style=\"margin: 0px 0px 1rem; border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><span style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ;\"><b>Departemen Informatika Fakultas Teknologi Industri (FTI) Universitas Atma Jaya Yogyakarta (UAJY)</b><br><br>bekerja sama dengan BlockDevID menyelenggarakan Seminar dan Workshop Blockchain &amp; Web3 Development yang bertempat di Ruang Auditorium Kampus III Gedung St. Bonaventura, pada Senin (9/2/2026). Kegiatan ini bertujuan untuk memperkenalkan teknologi blockchain dan Web3 kepada sivitas akademika serta masyarakat umum melalui pemaparan materi dan bimbingan teknis secara langsung oleh praktisi industri. Seminar dan workshop ini diikuti oleh peserta yang berasal dari lingkungan UAJY maupun luar UAJY. Selain itu, kegiatan ini juga dihadiri oleh peserta dari komunitas tuli dan dengar Daerah Istimewa Yogyakarta sebagai wujud komitmen terhadap inklusivitas dalam pengembangan teknologi. Seminar dan workshop ini mengusung tema “From Zero to Builder - Empowering Local Talents in a Decentralized Future” dan terdiri atas tiga sesi utama. Sesi pertama disampaikan oleh Dennis selaku Head of Community BlockDevID dengan materi Blockchain 101 &amp; Career Opportunity yang membahas pengenalan dasar teknologi blockchain serta peluang karir di bidang Web3. Sesi kedua dibawakan oleh Yanzero, Founder DevWeb3 Jogja, dengan topik How Web3 Products Are Actually Built yang mengulas proses pengembangan produk Web3 secara nyata. Sesi ketiga berupa coding workshop yang dipandu oleh Alex dari DevRel Base Indonesia, yang memberikan pendampingan teknis kepada peserta melalui praktik langsung pengembangan aplikasi berbasis Web3.</span></p><figure style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 1rem auto; text-align: center; width: 1152px; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><img src=\"https://inf.uajy.ac.id/be/uploads/716c2bc4-9559-44c6-9418-2c7c45ec7c9e?r=1774503605000\" alt=\"\" width=\"512\" style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; display: block; vertical-align: middle; max-height: 70vh; width: 1152px; object-fit: contain; margin: auto;\"></figure><p style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 0px 0px 1rem; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><span style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ;\">Dekan Fakultas Teknologi Industri (FTI) UAJY, Prof. Dr. Ir. Parama Kartika Dewa, S.P., S.T., M.T., IPU., dalam sambutannya menyampaikan apresiasi atas terselenggaranya kegiatan ini. Ia menekankan pentingnya kolaborasi antara perguruan tinggi dan industri dalam mempersiapkan sumber daya manusia yang adaptif terhadap perkembangan teknologi digital. Sementara itu, Ketua Departemen Informatika UAJY, Paulus Mudjihartono, S.T., M.T., Ph.D., menyampaikan bahwa pengenalan teknologi blockchain dan Web3 menjadi langkah strategis dalam memperluas wawasan mahasiswa terhadap teknologi informasi terkini yang memiliki potensi besar di masa depan.</span></p><p style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 0px 0px 1rem; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><span style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ;\">Salah satu peserta kegiatan, Marcella Averina, menyampaikan bahwa kegiatan ini memberikan pengalaman yang bermanfaat. “Acara ini menarik dan menambah wawasan karena blockchain masih jarang dibahas, terutama di bangku kuliah. Saya berharap kedepannya semakin banyak kegiatan serupa yang tidak hanya berfokus pada teori, tetapi juga memberikan pengalaman praktik secara langsung,” ungkapnya. Melalui penyelenggaraan seminar dan workshop ini, Departemen Informatika FTI UAJY berharap dapat memberikan kontribusi nyata dalam meningkatkan literasi teknologi blockchain dan Web3 serta mendorong pengembangan talenta digital.</span></p><figure style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 1rem auto; text-align: center; width: 1152px; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><img src=\"https://inf.uajy.ac.id/be/uploads/0688c46a-e6c9-4596-8255-e0f06cfeb0ff?r=1774503665000\" alt=\"\" width=\"512\" style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; display: block; vertical-align: middle; max-height: 70vh; width: 1152px; object-fit: contain; margin: auto;\"></figure>', 'aaaaaaaaaaaaa', '[{\"url\": \"/uploads/foto_baju_koki_930e3a088b314b4cb3706338a9171d10.jpg\", \"name\": \"foto_baju_koki_930e3a088b314b4cb3706338a9171d10.jpg\", \"mimeType\": \"\", \"size\": 0, \"previewable\": true, \"kind\": \"image\"}]', '[{\"url\": \"/uploads/Tanda_Tangan_Mick_Schumacher_a0c28248b91141529773d49c47298331.png\", \"name\": \"Tanda_Tangan_Mick_Schumacher_a0c28248b91141529773d49c47298331.png\", \"mimeType\": \"\", \"size\": 0, \"previewable\": true, \"kind\": \"image\"}, {\"url\": \"/uploads/Hasil_Pengujian_User_Flow_a065c9ffb9b64ca8a817aed2b26f8047.pdf\", \"name\": \"Hasil_Pengujian_User_Flow_a065c9ffb9b64ca8a817aed2b26f8047.pdf\", \"mimeType\": \"\", \"size\": 0, \"previewable\": true, \"kind\": \"pdf\"}]', 'published', NULL, '2026-05-01 06:51:12', '2026-05-01 11:56:02');

-- --------------------------------------------------------

--
-- Struktur dari tabel `news_categories`
--

CREATE TABLE `news_categories` (
  `id` varchar(100) NOT NULL,
  `name` varchar(255) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `order_index` int(11) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `news_categories`
--

INSERT INTO `news_categories` (`id`, `name`, `slug`, `description`, `order_index`, `created_at`, `updated_at`) VALUES
('cat-1777592900420', 'Umum', 'umum', '', 0, '2026-05-01 06:48:20', '2026-05-01 06:49:55'),
('cat-1777592913386', 'Crembo', 'crembo', '', 1, '2026-05-01 06:48:33', '2026-05-01 06:48:33'),
('cat-1777592921235', 'Oprec', 'oprec', '', 2, '2026-05-01 06:48:41', '2026-05-01 06:49:35'),
('cat-1777592972308', 'Camping', 'camping', '', 3, '2026-05-01 06:49:32', '2026-05-01 06:49:38');

-- --------------------------------------------------------

--
-- Struktur dari tabel `news_category_mapping`
--

CREATE TABLE `news_category_mapping` (
  `id` int(11) NOT NULL,
  `news_id` varchar(100) NOT NULL,
  `category_id` varchar(100) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `news_category_mapping`
--

INSERT INTO `news_category_mapping` (`id`, `news_id`, `category_id`, `created_at`) VALUES
(5, 'news-1777593072897', 'cat-1777592900420', '2026-05-01 11:56:02'),
(6, 'news-1777593072897', 'cat-1777592913386', '2026-05-01 11:56:02');

-- --------------------------------------------------------

--
-- Struktur dari tabel `organization_profiles`
--

CREATE TABLE `organization_profiles` (
  `id` varchar(100) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `attachment_url` text DEFAULT NULL,
  `order_index` int(11) DEFAULT 0,
  `is_visible` tinyint(1) DEFAULT 1,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `organization_profiles`
--

INSERT INTO `organization_profiles` (`id`, `title`, `description`, `attachment_url`, `order_index`, `is_visible`, `created_at`, `updated_at`) VALUES
('profile-1777560615559', 'Profil Organisasi - Test Update', 'Crembo Media adalah organisasi yang berdedikasi untuk mendukung kegiatan multimedia dan liturgi di komunitas. Visi kami adalah menjadi tulang punggung komunikasi visual dalam setiap kegiatan pelayanan.', '[{\"url\": \"uploads/fake-signature-word-vector_1777561240.jpg\", \"name\": \"fake-signature-word-vector_1777561240.jpg\", \"mimeType\": \"\", \"size\": 0, \"previewable\": true, \"kind\": \"image\"}]', 1, 1, '2026-04-30 21:50:15', '2026-05-01 03:59:00'),
('profile-1777561298872', 'Test 1 Oprec', 'aSsSA', '[{\"url\": \"uploads/fake-signature-word-vector_1777561296.jpg\", \"name\": \"fake-signature-word-vector_1777561296.jpg\", \"mimeType\": \"\", \"size\": 0, \"previewable\": true, \"kind\": \"image\"}]', 2, 1, '2026-04-30 22:01:38', '2026-05-01 05:52:10'),
('profile-1777561628347', 'asdasaaaaaaa', 'asdasdASas', '[]', 0, 1, '2026-04-30 22:07:08', '2026-05-01 04:03:52'),
('profile-1777582943778', 'Test Upload FIX', '<p style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 0px 0px 1rem; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><span style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ;\"><b>Departemen Informatika Fakultas Teknologi Industri (FTI) Universitas Atma Jaya Yogyakarta (UAJY) </b><br><br>bekerja sama dengan BlockDevID menyelenggarakan Seminar dan Workshop Blockchain &amp; Web3 Development yang bertempat di Ruang Auditorium Kampus III Gedung St. Bonaventura, pada Senin (9/2/2026). Kegiatan ini bertujuan untuk memperkenalkan teknologi blockchain dan Web3 kepada sivitas akademika serta masyarakat umum melalui pemaparan materi dan bimbingan teknis secara langsung oleh praktisi industri. Seminar dan workshop ini diikuti oleh peserta yang berasal dari lingkungan UAJY maupun luar UAJY. Selain itu, kegiatan ini juga dihadiri oleh peserta dari komunitas tuli dan dengar Daerah Istimewa Yogyakarta sebagai wujud komitmen terhadap inklusivitas dalam pengembangan teknologi. Seminar dan workshop ini mengusung tema “From Zero to Builder - Empowering Local Talents in a Decentralized Future” dan terdiri atas tiga sesi utama. Sesi pertama disampaikan oleh Dennis selaku Head of Community BlockDevID dengan materi Blockchain 101 &amp; Career Opportunity yang membahas pengenalan dasar teknologi blockchain serta peluang karir di bidang Web3. Sesi kedua dibawakan oleh Yanzero, Founder DevWeb3 Jogja, dengan topik How Web3 Products Are Actually Built yang mengulas proses pengembangan produk Web3 secara nyata. Sesi ketiga berupa coding workshop yang dipandu oleh Alex dari DevRel Base Indonesia, yang memberikan pendampingan teknis kepada peserta melalui praktik langsung pengembangan aplikasi berbasis Web3.</span></p><figure style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 1rem auto; text-align: center; width: 1152px; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><img src=\"https://inf.uajy.ac.id/be/uploads/716c2bc4-9559-44c6-9418-2c7c45ec7c9e?r=1774503605000\" alt=\"\" width=\"512\" style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; display: block; vertical-align: middle; max-height: 70vh; width: 1152px; object-fit: contain; margin: auto;\"></figure><p style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 0px 0px 1rem; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><span style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ;\">Dekan Fakultas Teknologi Industri (FTI) UAJY, Prof. Dr. Ir. Parama Kartika Dewa, S.P., S.T., M.T., IPU., dalam sambutannya menyampaikan apresiasi atas terselenggaranya kegiatan ini. Ia menekankan pentingnya kolaborasi antara perguruan tinggi dan industri dalam mempersiapkan sumber daya manusia yang adaptif terhadap perkembangan teknologi digital. Sementara itu, Ketua Departemen Informatika UAJY, Paulus Mudjihartono, S.T., M.T., Ph.D., menyampaikan bahwa pengenalan teknologi blockchain dan Web3 menjadi langkah strategis dalam memperluas wawasan mahasiswa terhadap teknologi informasi terkini yang memiliki potensi besar di masa depan.</span></p><p style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 0px 0px 1rem; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><span style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ;\">Salah satu peserta kegiatan, Marcella Averina, menyampaikan bahwa kegiatan ini memberikan pengalaman yang bermanfaat. “Acara ini menarik dan menambah wawasan karena blockchain masih jarang dibahas, terutama di bangku kuliah. Saya berharap kedepannya semakin banyak kegiatan serupa yang tidak hanya berfokus pada teori, tetapi juga memberikan pengalaman praktik secara langsung,” ungkapnya. Melalui penyelenggaraan seminar dan workshop ini, Departemen Informatika FTI UAJY berharap dapat memberikan kontribusi nyata dalam meningkatkan literasi teknologi blockchain dan Web3 serta mendorong pengembangan talenta digital.</span></p><figure style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; margin: 1rem auto; text-align: center; width: 1152px; color: rgb(0, 0, 0); font-family: Poppins, Poppins;\"><img src=\"https://inf.uajy.ac.id/be/uploads/0688c46a-e6c9-4596-8255-e0f06cfeb0ff?r=1774503665000\" alt=\"\" width=\"512\" style=\"border-width: 0px; border-style: solid; border-color: rgb(238, 238, 238); --tw-border-spacing-x: 0; --tw-border-spacing-y: 0; --tw-translate-x: 0; --tw-translate-y: 0; --tw-rotate: 0; --tw-skew-x: 0; --tw-skew-y: 0; --tw-scale-x: 1; --tw-scale-y: 1; --tw-pan-x: ; --tw-pan-y: ; --tw-pinch-zoom: ; --tw-scroll-snap-strictness: proximity; --tw-gradient-from-position: ; --tw-gradient-via-position: ; --tw-gradient-to-position: ; --tw-ordinal: ; --tw-slashed-zero: ; --tw-numeric-figure: ; --tw-numeric-spacing: ; --tw-numeric-fraction: ; --tw-ring-inset: ; --tw-ring-offset-width: 0px; --tw-ring-offset-color: #fff; --tw-ring-color: rgb(33 150 243 / .5); --tw-ring-offset-shadow: 0 0 #0000; --tw-ring-shadow: 0 0 #0000; --tw-shadow: 0 0 #0000; --tw-shadow-colored: 0 0 #0000; --tw-blur: ; --tw-brightness: ; --tw-contrast: ; --tw-grayscale: ; --tw-hue-rotate: ; --tw-invert: ; --tw-saturate: ; --tw-sepia: ; --tw-drop-shadow: ; --tw-backdrop-blur: ; --tw-backdrop-brightness: ; --tw-backdrop-contrast: ; --tw-backdrop-grayscale: ; --tw-backdrop-hue-rotate: ; --tw-backdrop-invert: ; --tw-backdrop-opacity: ; --tw-backdrop-saturate: ; --tw-backdrop-sepia: ; display: block; vertical-align: middle; max-height: 70vh; width: 1152px; object-fit: contain; margin: auto;\"></figure>', '[{\"url\": \"/uploads/Hasil_Pengujian_User_Flow_b45b548eedd942b695e61b7d2a55121d.pdf\", \"name\": \"Hasil_Pengujian_User_Flow.pdf\", \"mimeType\": \"application/pdf\", \"size\": 361523, \"previewable\": true, \"kind\": \"pdf\"}]', 4, 1, '2026-05-01 04:02:23', '2026-05-01 06:22:15');

-- --------------------------------------------------------

--
-- Struktur dari tabel `sertifikat_config`
--

CREATE TABLE `sertifikat_config` (
  `id` int(11) NOT NULL,
  `ketua_name` varchar(255) DEFAULT 'Ketua Crembo Media',
  `pembina_name` varchar(255) DEFAULT 'Pembina Crembo Media',
  `ketua_sign_url` text DEFAULT NULL,
  `pembina_sign_url` text DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `sertifikat_config`
--

INSERT INTO `sertifikat_config` (`id`, `ketua_name`, `pembina_name`, `ketua_sign_url`, `pembina_sign_url`, `updated_at`) VALUES
(1, 'Pria Briliantama', 'Fransiskus Xaverius Harso Susanto', 'uploads/Tanda_Tangan_Mick_Schumacher_1777507332.png', 'uploads/fake-signature-word-vector_1777507334.jpg', '2026-04-30 07:02:15');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tentang_crembo_config`
--

CREATE TABLE `tentang_crembo_config` (
  `id` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `button_text` varchar(255) DEFAULT NULL,
  `button_link` varchar(255) DEFAULT NULL,
  `auto_seconds` int(11) DEFAULT 5
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tentang_crembo_config`
--

INSERT INTO `tentang_crembo_config` (`id`, `description`, `button_text`, `button_link`, `auto_seconds`) VALUES
(1, 'Ringkasan profil organisasi, visi pelayanan multimedia, serta peran Crembo dalam mendukung kegiatan liturgi dan agenda komunitas. Konten ini nantinya diatur dari panel admin setelah loginnn', 'Pelajari Lebih Lanjut', 'https://www.instagram.com/crembo_media?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==', 5);

-- --------------------------------------------------------

--
-- Struktur dari tabel `tentang_crembo_media`
--

CREATE TABLE `tentang_crembo_media` (
  `id` varchar(100) NOT NULL,
  `type` varchar(50) DEFAULT 'image',
  `url` text DEFAULT NULL,
  `order_index` int(11) DEFAULT 0,
  `is_visible` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tentang_crembo_media`
--

INSERT INTO `tentang_crembo_media` (`id`, `type`, `url`, `order_index`, `is_visible`) VALUES
('about-img-1777487364855-0', 'image', 'uploads/foto_baju_koki_1777487364.jpg', 2, 1),
('about-img-1777487374027-0', 'image', 'uploads/sertifikat-anggota-zxczxczxc_1777487374.jpg', 3, 1),
('vid-1777487425472', 'video', 'https://youtu.be/_GVYvIC-6fA?si=HRMlwiYHctAeuNeT', 1, 1);

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2025_05`
--

CREATE TABLE `tugas_2025_05` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2025_05`
--

INSERT INTO `tugas_2025_05` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Rafael', '2025-05-20', '18:00', 'Operator');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2025_06`
--

CREATE TABLE `tugas_2025_06` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2025_06`
--

INSERT INTO `tugas_2025_06` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Orel', '2025-06-03', '18:00', 'Supervisor'),
(2, 'Wima', '2025-06-03', '18:00', 'Kameramen');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2025_07`
--

CREATE TABLE `tugas_2025_07` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2025_07`
--

INSERT INTO `tugas_2025_07` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Botun', '2025-07-06', '10:00', 'Operator'),
(2, 'Botun', '2025-07-03', '18:00', 'Supervisor'),
(3, 'Botun', '2025-07-10', '18:00', 'Kameramen'),
(4, 'Regio', '2025-07-13', '19:00', 'Supervisor'),
(5, 'Dewi', '2025-07-14', '18:00', 'Operator'),
(6, 'Dewi', '2025-07-16', '18:00', 'Kameramen'),
(7, 'Dewi', '2025-07-17', '18:00', 'Supervisor'),
(8, 'Claire', '2025-07-10', '18:00', 'Supervisor'),
(9, 'Claire', '2025-07-16', '18:00', 'Supervisor'),
(10, 'Jose', '2025-07-02', '18:00', 'Supervisor'),
(11, 'Jose', '2025-07-23', '18:00', 'Supervisor'),
(12, 'Jose', '2025-07-14', '18:00', 'Kameramen'),
(13, 'There', '2025-07-06', '19:00', 'Operator'),
(14, 'There', '2025-07-20', '10:00', 'Operator'),
(15, 'Florencia', '2025-07-17', '18:00', 'Kameramen'),
(16, 'Floren', '2025-07-06', '19:00', 'Kameramen'),
(17, 'Orel', '2025-07-02', '18:00', 'Kameramen'),
(18, 'Orel', '2025-07-23', '18:00', 'Kameramen'),
(19, 'Wima', '2025-07-02', '18:00', 'Operator'),
(20, 'Wima', '2025-07-23', '18:00', 'Operator'),
(21, 'Rossa', '2025-07-14', '18:00', 'Supervisor'),
(22, 'Tyas', '2025-07-21', '18:00', 'Operator'),
(23, 'Tyas', '2025-07-24', '18:00', 'Kameramen'),
(24, 'Noel', '2025-07-06', '19:00', 'Supervisor'),
(25, 'Noel', '2025-07-20', '17:00', 'Supervisor'),
(26, 'Noel', '2025-07-27', '19:00', 'Supervisor'),
(27, 'Belinda', '2025-07-18', '18:00', 'Supervisor'),
(28, 'Belinda', '2025-07-24', '18:00', 'Supervisor'),
(29, 'Tyas', '2025-07-18', '18:00', 'Kameramen'),
(30, 'Belinda', '2025-07-21', '18:00', 'Supervisor'),
(31, 'Tita', '2025-07-06', '10:00', 'Kameramen'),
(32, 'Tyas', '2025-07-13', '19:00', 'Kameramen'),
(33, 'Tita', '2025-07-16', '18:00', 'Operator'),
(34, 'Rossa', '2025-07-06', '10:00', 'Supervisor'),
(35, 'Toto', '2025-07-15', '18:00', 'Kameramen'),
(36, 'Lisa', '2025-07-17', '18:00', 'Operator'),
(37, 'Aurel', '2025-07-29', '18:00', 'Kameramen'),
(38, 'Aurel', '2025-07-15', '18:00', 'Supervisor'),
(39, 'Aurel', '2025-07-22', '18:00', 'Kameramen'),
(40, 'Jeni', '2025-07-06', '08:00', 'Operator'),
(41, 'Jeni', '2025-07-13', '08:00', 'Supervisor'),
(42, 'Rikha', '2025-07-06', '08:00', 'Supervisor'),
(43, 'Rikha', '2025-07-13', '08:00', 'Operator'),
(44, 'There', '2025-07-27', '19:00', 'Operator'),
(45, 'Aura', '2025-07-15', '18:00', 'Operator'),
(46, 'Aura', '2025-07-20', '17:00', 'Operator'),
(47, 'Aura', '2025-07-27', '19:00', 'Kameramen'),
(48, 'Floren', '2025-07-03', '18:00', 'Operator'),
(49, 'Vio', '2025-07-05', '18:00', 'Supervisor'),
(50, 'Vio', '2025-07-20', '10:00', 'Kameramen'),
(51, 'Vio', '2025-07-27', '10:00', 'Operator'),
(52, 'Putra', '2025-07-05', '18:00', 'Kameramen'),
(53, 'Putra', '2025-07-03', '18:00', 'Kameramen'),
(54, 'Bian', '2025-07-10', '18:00', 'Operator'),
(55, 'Bian', '2025-07-20', '17:00', 'Kameramen'),
(56, 'Ifa', '2025-07-13', '17:00', 'Supervisor'),
(57, 'Ifa', '2025-07-06', '17:00', 'Supervisor'),
(58, 'Ifa', '2025-07-27', '17:00', 'Supervisor'),
(59, 'Aura', '2025-07-13', '17:00', 'Kameramen'),
(60, 'There', '2025-07-13', '17:00', 'Operator'),
(61, 'Ketrin', '2025-07-11', '18:00', 'Operator'),
(62, 'Ketrin', '2025-07-13', '08:00', 'Kameramen'),
(63, 'Nadia', '2025-07-29', '18:00', 'Supervisor'),
(64, 'Lisa', '2025-07-29', '18:00', 'Operator'),
(65, 'Christoforus Tadeus', '2025-07-05', '18:00', 'Operator'),
(66, 'Christoforus Tadeus', '2025-07-04', '18:00', 'Supervisor'),
(67, 'Pria', '2025-07-22', '18:00', 'Operator'),
(68, 'Christoforus Tadeus', '2025-07-01', '18:00', 'Supervisor'),
(69, 'Nadia', '2025-07-04', '18:00', 'Kameramen'),
(70, 'Weka', '2025-07-11', '18:00', 'Supervisor'),
(71, 'Weka', '2025-07-04', '18:00', 'Operator'),
(72, 'There', '2025-07-20', '10:00', 'Supervisor'),
(73, 'Paul', '2025-07-01', '18:00', 'Operator'),
(74, 'Paul', '2025-07-09', '18:00', 'Supervisor'),
(75, 'Paul', '2025-07-12', '18:00', 'Supervisor'),
(76, 'Rosel', '2025-07-22', '18:00', 'Supervisor'),
(77, 'Rosel', '2025-07-21', '18:00', 'Kameramen'),
(78, 'Michel', '2025-07-09', '18:00', 'Operator'),
(79, 'Michel', '2025-07-08', '18:00', 'Kameramen'),
(80, 'Michel', '2025-07-11', '18:00', 'Kameramen'),
(81, 'Ketrin', '2025-07-18', '18:00', 'Operator'),
(82, 'Noel', '2025-07-01', '18:00', 'Kameramen'),
(83, 'Pria', '2025-07-27', '17:00', 'Operator'),
(84, 'Kanes', '2025-07-27', '17:00', 'Kameramen'),
(85, 'Kanes', '2025-07-06', '17:00', 'Kameramen'),
(86, 'Tita', '2025-07-06', '17:00', 'Operator'),
(87, 'Lisa', '2025-07-07', '18:00', 'Operator'),
(88, 'Floren', '2025-07-13', '10:00', 'Kameramen'),
(89, 'Toto', '2025-07-24', '18:00', 'Operator'),
(90, 'Rossa', '2025-07-07', '18:00', 'Supervisor'),
(91, 'Vista', '2025-07-07', '18:00', 'Kameramen'),
(92, 'Ketrin', '2025-07-06', '08:00', 'Kameramen'),
(93, 'Ketrin', '2025-07-09', '18:00', 'Kameramen'),
(94, 'Panji', '2025-07-08', '18:00', 'Operator'),
(95, 'Alta', '2025-07-08', '18:00', 'Supervisor'),
(96, 'Alta', '2025-07-27', '10:00', 'Supervisor'),
(101, 'Kanes', '2025-07-28', '18:00', 'Operator');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2025_08`
--

CREATE TABLE `tugas_2025_08` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2025_08`
--

INSERT INTO `tugas_2025_08` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Tyas', '2025-08-18', '18:00', 'Kameramen'),
(2, 'Regio', '2025-08-06', '18:00', 'Operator'),
(3, 'Regio', '2025-08-12', '18:00', 'Supervisor'),
(6, 'Ketrin', '2025-08-08', '18:00', 'Operator'),
(7, 'Tita', '2025-08-16', '18:00', 'Operator'),
(8, 'Veny', '2025-08-03', '10:00', 'Kameramen'),
(9, 'Veny', '2025-08-10', '08:00', 'Supervisor'),
(10, 'Noel', '2025-08-03', '19:00', 'Supervisor'),
(11, 'Noel', '2025-08-10', '19:00', 'Supervisor'),
(12, 'Noel', '2025-08-31', '19:00', 'Supervisor'),
(13, 'Belinda', '2025-08-19', '18:00', 'Supervisor'),
(14, 'Belinda', '2025-08-21', '18:00', 'Kameramen'),
(15, 'Belinda', '2025-08-26', '18:00', 'Supervisor'),
(16, 'Tita', '2025-08-24', '10:00', 'Kameramen'),
(17, 'Rossa', '2025-08-24', '10:00', 'Operator'),
(18, 'There', '2025-08-03', '19:00', 'Operator'),
(19, 'Tyas', '2025-08-06', '18:00', 'Kameramen'),
(20, 'There', '2025-08-31', '19:00', 'Operator'),
(21, 'There', '2025-08-24', '19:00', 'Operator'),
(22, 'Tyas', '2025-08-19', '18:00', 'Operator'),
(23, 'Tyas', '2025-08-21', '18:00', 'Operator'),
(24, 'Tyas', '2025-08-26', '18:00', 'Kameramen'),
(25, 'Aura', '2025-08-08', '18:00', 'Supervisor'),
(26, 'Tyas', '2025-08-12', '18:00', 'Kameramen'),
(27, 'Aura', '2025-08-23', '18:00', 'Operator'),
(28, 'Panji', '2025-08-03', '19:00', 'Kameramen'),
(29, 'Panji', '2025-08-24', '19:00', 'Supervisor'),
(30, 'Orel', '2025-08-18', '18:00', 'Supervisor'),
(31, 'Aurel', '2025-08-20', '18:00', 'Kameramen'),
(32, 'Aurel', '2025-08-19', '18:00', 'Kameramen'),
(33, 'Aurel', '2025-08-27', '18:00', 'Operator'),
(34, 'Regio', '2025-08-23', '18:00', 'Supervisor'),
(35, 'Tyas', '2025-08-23', '18:00', 'Kameramen'),
(36, 'Vio', '2025-08-02', '18:00', 'Supervisor'),
(37, 'Vio', '2025-08-16', '18:00', 'Supervisor'),
(38, 'Jeni', '2025-08-03', '08:00', 'Kameramen'),
(39, 'Jeni', '2025-08-10', '08:00', 'Operator'),
(40, 'Jeni', '2025-08-24', '08:00', 'Supervisor'),
(41, 'Rikha', '2025-08-03', '08:00', 'Operator'),
(42, 'Rikha', '2025-08-10', '08:00', 'Kameramen'),
(43, 'Rikha', '2025-08-24', '08:00', 'Kameramen'),
(44, 'Wima', '2025-08-27', '18:00', 'Kameramen'),
(45, 'Orel', '2025-08-27', '18:00', 'Supervisor'),
(46, 'Orel', '2025-08-20', '18:00', 'Operator'),
(47, 'Wima', '2025-08-20', '18:00', 'Supervisor'),
(48, 'Deva', '2025-08-08', '18:00', 'Kameramen'),
(49, 'Lisa', '2025-08-13', '18:00', 'Operator'),
(50, 'Wima', '2025-08-18', '18:00', 'Operator'),
(51, 'Lisa', '2025-08-25', '18:00', 'Operator'),
(52, 'Bian', '2025-08-10', '19:00', 'Operator'),
(53, 'Alta', '2025-08-25', '18:00', 'Supervisor'),
(54, 'Florencia', '2025-08-25', '18:00', 'Kameramen'),
(55, 'Bian', '2025-08-24', '10:00', 'Supervisor'),
(56, 'Claire', '2025-08-13', '18:00', 'Supervisor'),
(57, 'Alta', '2025-08-10', '19:00', 'Kameramen'),
(58, 'Florencia', '2025-08-16', '18:00', 'Kameramen'),
(59, 'Florencia', '2025-08-13', '18:00', 'Kameramen'),
(60, 'Claire', '2025-08-06', '18:00', 'Supervisor'),
(61, 'Lisa', '2025-08-04', '18:00', 'Operator'),
(62, 'Christoforus Tadeus', '2025-08-01', '18:00', 'Supervisor'),
(63, 'Christoforus Tadeus', '2025-08-11', '18:00', 'Supervisor'),
(64, 'Asha', '2025-08-21', '18:00', 'Supervisor'),
(65, 'Asha', '2025-08-24', '19:00', 'Kameramen'),
(66, 'Asha', '2025-08-31', '19:00', 'Kameramen'),
(67, 'Nadia', '2025-08-04', '18:00', 'Kameramen'),
(68, 'Nadia', '2025-08-11', '18:00', 'Kameramen'),
(69, 'Ketrin', '2025-08-14', '18:00', 'Operator'),
(70, 'Deva', '2025-08-14', '18:00', 'Supervisor'),
(71, 'Rossa', '2025-08-26', '18:00', 'Operator'),
(72, 'Paul', '2025-08-05', '18:00', 'Supervisor'),
(73, 'Paul', '2025-08-07', '18:00', 'Supervisor'),
(74, 'Deva', '2025-08-04', '18:00', 'Supervisor'),
(75, 'Pria', '2025-08-02', '18:00', 'Kameramen'),
(76, 'Pria', '2025-08-03', '17:00', 'Supervisor'),
(77, 'Satrio', '2025-08-01', '18:00', 'Operator'),
(78, 'Paul', '2025-08-09', '18:00', 'Supervisor'),
(79, 'Satrio', '2025-08-02', '18:00', 'Operator'),
(80, 'Aura', '2025-08-03', '17:00', 'Operator'),
(81, 'Floren', '2025-08-03', '17:00', 'Kameramen'),
(82, 'Floren', '2025-08-09', '18:00', 'Operator'),
(83, 'Weka', '2025-08-05', '18:00', 'Operator'),
(84, 'Weka', '2025-08-07', '18:00', 'Operator'),
(85, 'Floren', '2025-08-12', '18:00', 'Operator'),
(86, 'Weka', '2025-08-09', '18:00', 'Kameramen'),
(87, 'Christoforus Tadeus', '2025-08-22', '18:00', 'Supervisor'),
(88, 'Veny', '2025-08-01', '18:00', 'Kameramen'),
(89, 'Michel', '2025-08-05', '18:00', 'Kameramen'),
(90, 'Michel', '2025-08-28', '18:00', 'Supervisor'),
(91, 'Michel', '2025-08-07', '18:00', 'Kameramen'),
(92, 'Jose', '2025-08-28', '18:00', 'Kameramen'),
(93, 'Nawung', '2025-08-03', '10:00', 'Supervisor'),
(94, 'Putra', '2025-08-14', '18:00', 'Kameramen'),
(95, 'Putra', '2025-08-22', '18:00', 'Kameramen'),
(96, 'Kanes', '2025-08-28', '18:00', 'Operator'),
(97, 'Chris', '2025-08-03', '08:00', 'Supervisor'),
(98, 'Chris', '2025-08-03', '10:00', 'Operator'),
(99, 'Ifa', '2025-08-11', '18:00', 'Operator'),
(100, 'Ifa', '2025-08-22', '18:00', 'Operator'),
(101, 'Ifa', '2025-08-24', '08:00', 'Operator'),
(102, 'There', '2025-08-17', '19:00', 'Operator'),
(103, 'Ketrin', '2025-08-29', '18:00', 'Operator'),
(104, 'Toto', '2025-08-10', '10:00', 'Supervisor'),
(105, 'There', '2025-08-10', '10:00', 'Operator'),
(106, 'Naresh', '2025-08-10', '17:00', 'Operator'),
(107, 'Naresh', '2025-08-29', '18:00', 'Kameramen'),
(108, 'Naresh', '2025-08-30', '18:00', 'Supervisor'),
(109, 'Nawung', '2025-08-29', '18:00', 'Supervisor'),
(110, 'Nawung', '2025-08-15', '18:00', 'Operator'),
(111, 'Vio', '2025-08-15', '18:00', 'Kameramen'),
(112, 'Pria', '2025-08-30', '18:00', 'Kameramen'),
(113, 'Yuta', '2025-08-17', '19:00', 'Supervisor'),
(114, 'Yuta', '2025-08-31', '17:00', 'Kameramen'),
(115, 'Bima', '2025-08-15', '18:00', 'Supervisor'),
(116, 'Bima', '2025-08-30', '18:00', 'Operator'),
(117, 'Ketrin', '2025-08-17', '08:00', 'Operator'),
(118, 'Ketrin', '2025-08-31', '17:00', 'Supervisor'),
(119, 'Kinan', '2025-08-10', '17:00', 'Kameramen'),
(120, 'Aura', '2025-08-31', '17:00', 'Operator'),
(121, 'Panji', '2025-08-10', '17:00', 'Supervisor'),
(122, 'Putra', '2025-08-17', '17:00', 'Kameramen'),
(123, 'Toto', '2025-08-17', '17:00', 'Operator'),
(124, 'Satrio', '2025-08-17', '10:00', 'Kameramen'),
(125, 'There', '2025-08-24', '17:00', 'Operator');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2025_09`
--

CREATE TABLE `tugas_2025_09` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2025_09`
--

INSERT INTO `tugas_2025_09` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Noel', '2025-09-07', '17:00', 'Supervisor'),
(2, 'Noel', '2025-09-14', '19:00', 'Supervisor'),
(3, 'Noel', '2025-09-28', '17:00', 'Supervisor'),
(4, 'Aura', '2025-09-02', '18:00', 'Supervisor'),
(5, 'Aura', '2025-09-14', '17:00', 'Operator'),
(6, 'Aura', '2025-09-27', '18:00', 'Operator'),
(7, 'Jose', '2025-09-23', '18:00', 'Supervisor'),
(8, 'Jose', '2025-09-10', '18:00', 'Supervisor'),
(9, 'Jose', '2025-09-03', '18:00', 'Supervisor'),
(10, 'Bian', '2025-09-04', '18:00', 'Supervisor'),
(11, 'Bian', '2025-09-14', '10:00', 'Operator'),
(12, 'Bian', '2025-09-25', '18:00', 'Supervisor'),
(13, 'Ata Surya', '2025-09-02', '18:00', 'Operator'),
(14, 'Ata Surya', '2025-09-03', '18:00', 'Kameramen'),
(15, 'Ata Surya', '2025-09-04', '18:00', 'Operator'),
(16, 'Rossa', '2025-09-28', '10:00', 'Operator'),
(17, 'Tita', '2025-09-28', '10:00', 'Kameramen'),
(18, 'Rossa', '2025-09-17', '18:00', 'Operator'),
(19, 'Tita', '2025-09-17', '18:00', 'Kameramen'),
(20, 'Ketrin', '2025-09-16', '18:00', 'Operator'),
(21, 'Aura', '2025-09-07', '17:00', 'Operator'),
(22, 'Rosel', '2025-09-24', '18:00', 'Supervisor'),
(23, 'Jeni', '2025-09-07', '08:00', 'Supervisor'),
(24, 'Jeni', '2025-09-14', '08:00', 'Operator'),
(25, 'Rikha', '2025-09-07', '08:00', 'Operator'),
(26, 'Rikha', '2025-09-14', '08:00', 'Kameramen'),
(27, 'Jeni', '2025-09-21', '08:00', 'Kameramen'),
(28, 'Rikha', '2025-09-21', '08:00', 'Operator'),
(29, 'Tyas', '2025-09-11', '18:00', 'Operator'),
(30, 'Deva', '2025-09-11', '18:00', 'Supervisor'),
(31, 'Aurel', '2025-09-02', '18:00', 'Kameramen'),
(32, 'Belinda', '2025-09-04', '18:00', 'Kameramen'),
(33, 'Belinda', '2025-09-11', '18:00', 'Kameramen'),
(34, 'Belinda', '2025-09-08', '18:00', 'Supervisor'),
(35, 'Tyas', '2025-09-08', '18:00', 'Kameramen'),
(36, 'Ifa', '2025-09-27', '18:00', 'Kameramen'),
(37, 'Ifa', '2025-09-28', '10:00', 'Supervisor'),
(38, 'Aurel', '2025-09-03', '18:00', 'Operator'),
(39, 'Asha', '2025-09-14', '17:00', 'Kameramen'),
(40, 'Vio', '2025-09-06', '18:00', 'Operator'),
(41, 'There', '2025-09-07', '19:00', 'Operator'),
(42, 'Vio', '2025-09-20', '18:00', 'Operator'),
(43, 'Vio', '2025-09-27', '18:00', 'Supervisor'),
(44, 'There', '2025-09-28', '19:00', 'Operator'),
(45, 'There', '2025-09-14', '19:00', 'Operator'),
(46, 'Asha', '2025-09-18', '18:00', 'Operator'),
(47, 'There', '2025-09-21', '19:00', 'Operator'),
(48, 'Kanes', '2025-09-17', '18:00', 'Supervisor'),
(49, 'Asha', '2025-09-24', '18:00', 'Kameramen'),
(50, 'Kanes', '2025-09-19', '18:00', 'Kameramen'),
(51, 'Michel', '2025-09-09', '18:00', 'Operator'),
(52, 'Michel', '2025-09-16', '18:00', 'Supervisor'),
(53, 'Michel', '2025-09-18', '18:00', 'Kameramen'),
(54, 'Florencia', '2025-09-18', '18:00', 'Supervisor'),
(55, 'Alta', '2025-09-14', '10:00', 'Supervisor'),
(56, 'Botun', '2025-09-16', '18:00', 'Kameramen'),
(57, 'Botun', '2025-09-24', '18:00', 'Operator'),
(58, 'Botun', '2025-09-28', '17:00', 'Kameramen'),
(59, 'Satrio', '2025-09-30', '18:00', 'Kameramen'),
(60, 'Satrio', '2025-09-29', '18:00', 'Kameramen'),
(61, 'Lisa', '2025-09-01', '18:00', 'Operator'),
(62, 'Christoforus Tadeus', '2025-09-01', '18:00', 'Supervisor'),
(63, 'Floren', '2025-09-07', '19:00', 'Kameramen'),
(64, 'Orel', '2025-09-09', '18:00', 'Supervisor'),
(65, 'Orel', '2025-09-30', '18:00', 'Supervisor'),
(66, 'Orel', '2025-09-22', '18:00', 'Operator'),
(67, 'Lisa', '2025-09-15', '18:00', 'Operator'),
(68, 'Ketrin', '2025-09-29', '18:00', 'Supervisor'),
(69, 'Nawung', '2025-09-07', '19:00', 'Supervisor'),
(70, 'Nawung', '2025-09-14', '19:00', 'Kameramen'),
(71, 'Putra', '2025-09-09', '18:00', 'Kameramen'),
(72, 'Putra', '2025-09-10', '18:00', 'Kameramen'),
(73, 'Chris', '2025-09-07', '17:00', 'Kameramen'),
(74, 'Chris', '2025-09-06', '18:00', 'Kameramen'),
(75, 'Chris', '2025-09-14', '17:00', 'Supervisor'),
(76, 'Toto', '2025-09-12', '18:00', 'Kameramen'),
(77, 'Toto', '2025-09-14', '10:00', 'Kameramen'),
(78, 'Tyas', '2025-09-25', '18:00', 'Kameramen'),
(79, 'Claire', '2025-09-15', '18:00', 'Supervisor'),
(80, 'Claire', '2025-09-22', '18:00', 'Kameramen'),
(81, 'Panji', '2025-09-21', '10:00', 'Supervisor'),
(82, 'Panji', '2025-09-07', '10:00', 'Supervisor'),
(83, 'Panji', '2025-09-21', '19:00', 'Supervisor'),
(84, 'Bian', '2025-09-06', '18:00', 'Supervisor'),
(85, 'Rossa', '2025-09-08', '18:00', 'Operator'),
(86, 'Nadia', '2025-09-15', '18:00', 'Kameramen'),
(87, 'Christoforus Tadeus', '2025-09-14', '08:00', 'Supervisor'),
(88, 'Christoforus Tadeus', '2025-09-07', '08:00', 'Kameramen'),
(89, 'Alta', '2025-09-12', '18:00', 'Supervisor'),
(90, 'Weka', '2025-09-05', '18:00', 'Operator'),
(91, 'Weka', '2025-09-23', '18:00', 'Kameramen'),
(92, 'Wima', '2025-09-05', '18:00', 'Supervisor'),
(93, 'Wima', '2025-09-12', '18:00', 'Operator'),
(94, 'Wima', '2025-09-25', '18:00', 'Operator'),
(95, 'Weka', '2025-09-10', '18:00', 'Operator'),
(96, 'Pria', '2025-09-13', '18:00', 'Supervisor'),
(97, 'Pria', '2025-09-23', '18:00', 'Operator'),
(98, 'Pria', '2025-09-29', '18:00', 'Operator'),
(99, 'Florencia', '2025-09-07', '10:00', 'Kameramen'),
(100, 'Floren', '2025-09-05', '18:00', 'Kameramen'),
(101, 'Ifa', '2025-09-07', '10:00', 'Operator'),
(102, 'Paul', '2025-09-13', '18:00', 'Operator'),
(103, 'Vista', '2025-09-22', '18:00', 'Supervisor'),
(104, 'Paul', '2025-09-20', '18:00', 'Kameramen'),
(105, 'Paul', '2025-09-28', '17:00', 'Operator'),
(106, 'Rafael', '2025-09-13', '18:00', 'Kameramen'),
(107, 'Rafael', '2025-09-20', '18:00', 'Supervisor'),
(108, 'Rafael', '2025-09-26', '18:00', 'Operator'),
(109, 'Claire', '2025-09-26', '18:00', 'Kameramen'),
(110, 'Bima', '2025-09-21', '08:00', 'Supervisor'),
(111, 'Bima', '2025-09-26', '18:00', 'Supervisor'),
(112, 'Bima', '2025-09-30', '18:00', 'Operator'),
(113, 'Nadia', '2025-09-21', '19:00', 'Kameramen'),
(114, 'Nadia', '2025-09-28', '08:00', 'Operator'),
(115, 'Tita', '2025-09-28', '08:00', 'Kameramen'),
(116, 'Deva', '2025-09-28', '19:00', 'Supervisor'),
(117, 'Veny', '2025-09-21', '17:00', 'Kameramen'),
(118, 'Veny', '2025-09-28', '19:00', 'Kameramen'),
(119, 'Naresh', '2025-09-28', '08:00', 'Supervisor'),
(120, 'Deva', '2025-09-21', '17:00', 'Supervisor'),
(121, 'There', '2025-09-21', '10:00', 'Operator');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2025_10`
--

CREATE TABLE `tugas_2025_10` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2025_10`
--

INSERT INTO `tugas_2025_10` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'There', '2025-10-05', '19:00', 'Operator'),
(2, 'Belinda', '2025-10-06', '18:00', 'Kameramen'),
(3, 'Belinda', '2025-10-09', '18:00', 'Supervisor'),
(4, 'Belinda', '2025-10-15', '18:00', 'Supervisor'),
(5, 'Tyas', '2025-10-06', '18:00', 'Operator'),
(6, 'Tyas', '2025-10-09', '18:00', 'Kameramen'),
(7, 'Tyas', '2025-10-15', '18:00', 'Operator'),
(8, 'Jose', '2025-10-02', '18:00', 'Supervisor'),
(9, 'Jose', '2025-10-10', '18:00', 'Kameramen'),
(10, 'Jose', '2025-10-23', '18:00', 'Supervisor'),
(11, 'Wima', '2025-10-22', '18:00', 'Operator'),
(12, 'Wima', '2025-10-23', '18:00', 'Kameramen'),
(13, 'Wima', '2025-10-29', '18:00', 'Supervisor'),
(14, 'Rafael', '2025-10-11', '18:00', 'Kameramen'),
(15, 'Rafael', '2025-10-18', '18:00', 'Kameramen'),
(16, 'Orel', '2025-10-22', '18:00', 'Kameramen'),
(17, 'Rafael', '2025-10-04', '18:00', 'Kameramen'),
(18, 'Orel', '2025-10-29', '18:00', 'Operator'),
(19, 'Orel', '2025-10-13', '18:00', 'Supervisor'),
(20, 'Nadia', '2025-10-10', '18:00', 'Supervisor'),
(21, 'There', '2025-10-12', '19:00', 'Supervisor'),
(22, 'There', '2025-10-26', '08:00', 'Supervisor'),
(23, 'There', '2025-10-19', '19:00', 'Operator'),
(24, 'Vio', '2025-10-04', '18:00', 'Operator'),
(25, 'Vio', '2025-10-11', '18:00', 'Supervisor'),
(26, 'Vio', '2025-10-18', '18:00', 'Operator'),
(27, 'Noel', '2025-10-05', '17:00', 'Supervisor'),
(28, 'Noel', '2025-10-19', '17:00', 'Supervisor'),
(29, 'Noel', '2025-10-26', '19:00', 'Supervisor'),
(30, 'Christoforus Tadeus', '2025-10-01', '18:00', 'Supervisor'),
(31, 'Christoforus Tadeus', '2025-10-07', '18:00', 'Supervisor'),
(32, 'Aura', '2025-10-12', '19:00', 'Operator'),
(33, 'Aurel', '2025-10-06', '18:00', 'Supervisor'),
(34, 'Aurel', '2025-10-07', '18:00', 'Kameramen'),
(35, 'Bian', '2025-10-05', '17:00', 'Operator'),
(36, 'Bian', '2025-10-14', '18:00', 'Supervisor'),
(37, 'Bian', '2025-10-19', '17:00', 'Operator'),
(38, 'Putra', '2025-10-01', '18:00', 'Kameramen'),
(39, 'Putra', '2025-10-02', '18:00', 'Kameramen'),
(40, 'Putra', '2025-10-08', '18:00', 'Kameramen'),
(41, 'Jeni', '2025-10-05', '08:00', 'Kameramen'),
(42, 'Ketrin', '2025-10-03', '18:00', 'Operator'),
(43, 'Rikha', '2025-10-05', '08:00', 'Operator'),
(44, 'Alta', '2025-10-05', '17:00', 'Kameramen'),
(45, 'Regio', '2025-10-12', '17:00', 'Supervisor'),
(46, 'Tyas', '2025-10-12', '17:00', 'Operator'),
(47, 'Rossa', '2025-10-09', '18:00', 'Operator'),
(48, 'Rossa', '2025-10-19', '08:00', 'Operator'),
(49, 'Tita', '2025-10-08', '18:00', 'Operator'),
(50, 'Tita', '2025-10-26', '10:00', 'Operator'),
(51, 'Rossa', '2025-10-26', '10:00', 'Supervisor'),
(52, 'Tita', '2025-10-19', '08:00', 'Kameramen'),
(53, 'Botun', '2025-10-08', '18:00', 'Supervisor'),
(54, 'Botun', '2025-10-16', '18:00', 'Supervisor'),
(55, 'Botun', '2025-10-21', '18:00', 'Operator'),
(56, 'Paul', '2025-10-04', '18:00', 'Supervisor'),
(57, 'Paul', '2025-10-01', '18:00', 'Operator'),
(58, 'Paul', '2025-10-02', '18:00', 'Operator'),
(59, 'Deva', '2025-10-03', '18:00', 'Kameramen'),
(60, 'Chris', '2025-10-12', '19:00', 'Kameramen'),
(61, 'Chris', '2025-10-19', '17:00', 'Kameramen'),
(62, 'Ifa', '2025-10-12', '10:00', 'Kameramen'),
(63, 'Ifa', '2025-10-25', '18:00', 'Kameramen'),
(64, 'Ifa', '2025-10-24', '18:00', 'Supervisor'),
(65, 'Asha', '2025-10-29', '18:00', 'Kameramen'),
(66, 'Pria', '2025-10-05', '19:00', 'Supervisor'),
(67, 'Pria', '2025-10-19', '08:00', 'Supervisor'),
(68, 'Michel', '2025-10-07', '18:00', 'Operator'),
(69, 'Michel', '2025-10-16', '18:00', 'Operator'),
(70, 'Michel', '2025-10-22', '18:00', 'Supervisor'),
(71, 'Asha', '2025-10-23', '18:00', 'Operator'),
(72, 'Asha', '2025-10-19', '19:00', 'Kameramen'),
(73, 'Nawung', '2025-10-26', '19:00', 'Kameramen'),
(74, 'Nawung', '2025-10-18', '18:00', 'Supervisor'),
(75, 'Naresh', '2025-10-05', '19:00', 'Kameramen'),
(76, 'Naresh', '2025-10-13', '18:00', 'Operator'),
(77, 'Naresh', '2025-10-28', '18:00', 'Kameramen'),
(78, 'Christoforus Tadeus', '2025-10-03', '18:00', 'Supervisor'),
(79, 'Ketrin', '2025-10-28', '18:00', 'Supervisor'),
(80, 'Weka', '2025-10-11', '18:00', 'Operator'),
(81, 'Weka', '2025-10-14', '18:00', 'Operator'),
(82, 'Weka', '2025-10-16', '18:00', 'Kameramen'),
(83, 'Claire', '2025-10-21', '18:00', 'Supervisor'),
(84, 'Claire', '2025-10-30', '18:00', 'Supervisor'),
(85, 'Claire', '2025-10-14', '18:00', 'Kameramen'),
(86, 'Floren', '2025-10-12', '17:00', 'Kameramen'),
(87, 'Floren', '2025-10-19', '10:00', 'Operator'),
(88, 'Dewi', '2025-10-28', '18:00', 'Operator'),
(89, 'Dewi', '2025-10-27', '18:00', 'Supervisor'),
(90, 'Satrio', '2025-10-13', '18:00', 'Kameramen'),
(91, 'Satrio', '2025-10-15', '18:00', 'Kameramen'),
(92, 'Satrio', '2025-10-17', '18:00', 'Supervisor'),
(93, 'Lisa', '2025-10-20', '18:00', 'Operator'),
(94, 'Lisa', '2025-10-27', '18:00', 'Operator'),
(95, 'Deva', '2025-10-26', '17:00', 'Kameramen'),
(96, 'Deva', '2025-10-19', '19:00', 'Supervisor'),
(97, 'Panji', '2025-10-05', '10:00', 'Supervisor'),
(98, 'Panji', '2025-10-17', '18:00', 'Kameramen'),
(99, 'Panji', '2025-10-24', '18:00', 'Kameramen'),
(100, 'Bima', '2025-10-05', '10:00', 'Operator'),
(101, 'Veny', '2025-10-05', '08:00', 'Supervisor'),
(102, 'Veny', '2025-10-10', '18:00', 'Operator'),
(103, 'Florencia', '2025-10-20', '18:00', 'Kameramen'),
(104, 'Florencia', '2025-10-19', '10:00', 'Kameramen'),
(105, 'Florencia', '2025-10-24', '18:00', 'Operator'),
(106, 'Kanes', '2025-10-17', '18:00', 'Operator'),
(107, 'Kanes', '2025-10-21', '18:00', 'Kameramen'),
(108, 'Kanes', '2025-10-26', '17:00', 'Operator'),
(109, 'Alta', '2025-10-25', '18:00', 'Operator'),
(110, 'Bima', '2025-10-20', '18:00', 'Supervisor'),
(111, 'Bima', '2025-10-25', '18:00', 'Supervisor'),
(112, 'Aura', '2025-10-26', '19:00', 'Operator'),
(113, 'Daflo', '2025-10-12', '08:00', 'Operator'),
(114, 'Daflo', '2025-10-19', '10:00', 'Supervisor'),
(115, 'Daflo', '2025-10-26', '17:00', 'Supervisor'),
(116, 'Panji', '2025-10-31', '18:00', 'Supervisor'),
(117, 'Nadia', '2025-10-27', '18:00', 'Kameramen'),
(118, 'Nadia', '2025-10-26', '08:00', 'Kameramen'),
(119, 'Ata Surya', '2025-10-05', '10:00', 'Kameramen'),
(120, 'Toto', '2025-10-12', '10:00', 'Operator'),
(121, 'Toto', '2025-10-26', '10:00', 'Kameramen'),
(122, 'Alta', '2025-10-12', '10:00', 'Supervisor'),
(123, 'Chris', '2025-10-31', '18:00', 'Kameramen'),
(124, 'There', '2025-10-30', '18:00', 'Operator'),
(125, 'Ata Surya', '2025-10-31', '18:00', 'Operator');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2025_11`
--

CREATE TABLE `tugas_2025_11` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2025_11`
--

INSERT INTO `tugas_2025_11` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'There', '2025-11-09', '19:00', 'Operator'),
(2, 'There', '2025-11-23', '19:00', 'Operator'),
(3, 'Rossa', '2025-11-09', '10:00', 'Operator'),
(4, 'Tita', '2025-11-09', '10:00', 'Kameramen'),
(5, 'Tita', '2025-11-16', '10:00', 'Operator'),
(6, 'Rossa', '2025-11-16', '10:00', 'Supervisor'),
(7, 'Noel', '2025-11-02', '17:00', 'Supervisor'),
(8, 'Noel', '2025-11-09', '17:00', 'Supervisor'),
(9, 'Noel', '2025-11-23', '17:00', 'Supervisor'),
(10, 'Belinda', '2025-11-06', '18:00', 'Supervisor'),
(11, 'Belinda', '2025-11-11', '18:00', 'Kameramen'),
(12, 'Belinda', '2025-11-18', '18:00', 'Supervisor'),
(13, 'Tyas', '2025-11-06', '18:00', 'Kameramen'),
(14, 'Tyas', '2025-11-11', '18:00', 'Operator'),
(15, 'Tyas', '2025-11-18', '18:00', 'Kameramen'),
(16, 'Tyas', '2025-11-18', '18:00', 'Operator'),
(17, 'Tita', '2025-11-23', '10:00', 'Operator'),
(18, 'Christoforus Tadeus', '2025-11-04', '18:00', 'Supervisor'),
(19, 'Weka', '2025-11-03', '18:00', 'Supervisor'),
(20, 'Weka', '2025-11-04', '18:00', 'Operator'),
(21, 'Weka', '2025-11-05', '18:00', 'Supervisor'),
(22, 'Bian', '2025-11-03', '18:00', 'Operator'),
(23, 'Bian', '2025-11-09', '17:00', 'Operator'),
(24, 'Bian', '2025-11-14', '18:00', 'Supervisor'),
(25, 'Floren', '2025-11-08', '18:00', 'Kameramen'),
(26, 'Dewi', '2025-11-12', '18:00', 'Operator'),
(27, 'Dewi', '2025-11-13', '18:00', 'Supervisor'),
(28, 'Dewi', '2025-11-17', '18:00', 'Kameramen'),
(29, 'Florencia', '2025-11-12', '18:00', 'Supervisor'),
(30, 'Ifa', '2025-11-09', '08:00', 'Operator'),
(31, 'Ifa', '2025-11-16', '08:00', 'Kameramen'),
(32, 'Aurel', '2025-11-12', '18:00', 'Kameramen'),
(33, 'Aura', '2025-11-23', '17:00', 'Operator'),
(34, 'Ata Surya', '2025-11-23', '17:00', 'Kameramen'),
(35, 'Noel', '2025-11-02', '08:00', 'Operator'),
(36, 'Christoforus Tadeus', '2025-11-02', '08:00', 'Supervisor'),
(37, 'Pria', '2025-11-16', '19:00', 'Supervisor'),
(38, 'Pria', '2025-11-30', '10:00', 'Supervisor'),
(39, 'Vio', '2025-11-01', '18:00', 'Operator'),
(40, 'Vio', '2025-11-07', '18:00', 'Operator'),
(41, 'Vio', '2025-11-08', '18:00', 'Operator'),
(42, 'There', '2025-11-16', '19:00', 'Operator'),
(43, 'Ketrin', '2025-11-13', '18:00', 'Operator'),
(44, 'Ketrin', '2025-11-08', '18:00', 'Supervisor'),
(45, 'Botun', '2025-11-03', '18:00', 'Kameramen'),
(46, 'Botun', '2025-11-05', '18:00', 'Operator'),
(47, 'Botun', '2025-11-25', '18:00', 'Supervisor'),
(48, 'Asha', '2025-11-06', '18:00', 'Operator'),
(49, 'Asha', '2025-11-04', '18:00', 'Kameramen'),
(50, 'Nawung', '2025-11-15', '18:00', 'Supervisor'),
(51, 'Nawung', '2025-11-23', '19:00', 'Supervisor'),
(52, 'Michel', '2025-11-11', '18:00', 'Supervisor'),
(53, 'Michel', '2025-11-20', '18:00', 'Operator'),
(54, 'Michel', '2025-11-27', '18:00', 'Operator'),
(55, 'Jose', '2025-11-19', '18:00', 'Kameramen'),
(56, 'Jose', '2025-11-26', '18:00', 'Supervisor'),
(57, 'Jose', '2025-11-13', '18:00', 'Kameramen'),
(58, 'Wima', '2025-11-05', '18:00', 'Kameramen'),
(59, 'Wima', '2025-11-26', '18:00', 'Kameramen'),
(60, 'Wima', '2025-11-20', '18:00', 'Supervisor'),
(61, 'Orel', '2025-11-20', '18:00', 'Kameramen'),
(62, 'Orel', '2025-11-26', '18:00', 'Operator'),
(63, 'Floren', '2025-11-22', '18:00', 'Kameramen'),
(64, 'There', '2025-11-02', '10:00', 'Operator'),
(65, 'Satrio', '2025-11-25', '18:00', 'Kameramen'),
(66, 'Orel', '2025-11-27', '18:00', 'Supervisor'),
(67, 'Satrio', '2025-11-28', '18:00', 'Supervisor'),
(68, 'Putra', '2025-11-10', '18:00', 'Kameramen'),
(69, 'Putra', '2025-11-17', '18:00', 'Supervisor'),
(70, 'Putra', '2025-11-19', '18:00', 'Supervisor'),
(71, 'Satrio', '2025-11-24', '18:00', 'Kameramen'),
(72, 'Ketrin', '2025-11-02', '08:00', 'Kameramen'),
(73, 'Naresh', '2025-11-02', '17:00', 'Operator'),
(74, 'Nadia', '2025-11-02', '19:00', 'Operator'),
(75, 'Lisa', '2025-11-02', '17:00', 'Kameramen'),
(76, 'Rafael', '2025-11-02', '10:00', 'Supervisor'),
(77, 'Paul', '2025-11-02', '19:00', 'Supervisor'),
(78, 'Panji', '2025-11-02', '19:00', 'Kameramen'),
(79, 'Kanes', '2025-11-07', '18:00', 'Kameramen'),
(80, 'Toto', '2025-11-02', '10:00', 'Kameramen'),
(81, 'Panji', '2025-11-09', '17:00', 'Kameramen'),
(82, 'Panji', '2025-11-09', '19:00', 'Supervisor'),
(83, 'Nadia', '2025-11-23', '10:00', 'Supervisor'),
(84, 'Nadia', '2025-11-10', '18:00', 'Supervisor'),
(85, 'Lisa', '2025-11-10', '18:00', 'Operator'),
(86, 'Lisa', '2025-11-17', '18:00', 'Operator'),
(87, 'Deva', '2025-11-30', '19:00', 'Supervisor'),
(88, 'Deva', '2025-11-09', '19:00', 'Kameramen'),
(89, 'Deva', '2025-11-23', '19:00', 'Kameramen'),
(90, 'Aura', '2025-11-30', '17:00', 'Operator'),
(91, 'Pria', '2025-11-23', '08:00', 'Supervisor'),
(92, 'Nawung', '2025-11-30', '19:00', 'Kameramen'),
(93, 'Asha', '2025-11-14', '18:00', 'Operator'),
(94, 'Aura', '2025-11-16', '17:00', 'Operator'),
(95, 'Bima', '2025-11-15', '18:00', 'Operator'),
(96, 'Bima', '2025-11-24', '18:00', 'Supervisor'),
(97, 'Bima', '2025-11-30', '19:00', 'Operator'),
(98, 'Claire', '2025-11-09', '08:00', 'Kameramen'),
(99, 'Claire', '2025-11-16', '08:00', 'Operator'),
(100, 'Florencia', '2025-11-22', '18:00', 'Operator'),
(101, 'Claire', '2025-11-29', '18:00', 'Supervisor'),
(102, 'Ifa', '2025-11-19', '18:00', 'Operator'),
(103, 'Kanes', '2025-11-23', '10:00', 'Kameramen'),
(104, 'Kanes', '2025-11-30', '17:00', 'Kameramen'),
(105, 'Chris', '2025-11-28', '18:00', 'Operator'),
(106, 'Chris', '2025-11-23', '08:00', 'Operator'),
(107, 'Chris', '2025-11-16', '19:00', 'Kameramen'),
(108, 'Paul', '2025-11-16', '10:00', 'Kameramen'),
(109, 'Naresh', '2025-11-14', '18:00', 'Kameramen'),
(110, 'Naresh', '2025-11-25', '18:00', 'Operator'),
(111, 'Paul', '2025-11-07', '18:00', 'Supervisor'),
(112, 'Rossa', '2025-11-27', '18:00', 'Kameramen'),
(113, 'Rafael', '2025-11-28', '18:00', 'Kameramen'),
(114, 'Rafael', '2025-11-16', '17:00', 'Supervisor'),
(115, 'Floren', '2025-11-30', '08:00', 'Operator'),
(116, 'Toto', '2025-11-09', '10:00', 'Supervisor'),
(117, 'Toto', '2025-11-15', '18:00', 'Kameramen'),
(118, 'Daflo', '2025-11-16', '17:00', 'Kameramen'),
(119, 'Daflo', '2025-11-21', '18:00', 'Supervisor'),
(120, 'Daflo', '2025-11-23', '08:00', 'Kameramen'),
(121, 'Asha', '2025-11-24', '18:00', 'Operator'),
(122, 'Alta', '2025-11-22', '18:00', 'Supervisor'),
(123, 'There', '2025-11-30', '10:00', 'Operator'),
(124, 'Asha', '2025-11-30', '10:00', 'Kameramen'),
(125, 'There', '2025-11-21', '18:00', 'Operator'),
(126, 'Panji', '2025-11-21', '18:00', 'Kameramen'),
(127, 'Bian', '2025-11-29', '18:00', 'Kameramen'),
(128, 'Jose', '2025-11-29', '18:00', 'Operator'),
(129, 'Putra', '2025-11-30', '17:00', 'Supervisor'),
(130, 'Weka', '2025-11-30', '08:00', 'Supervisor'),
(131, 'Michel', '2025-11-30', '08:00', 'Kameramen');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2025_12`
--

CREATE TABLE `tugas_2025_12` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2025_12`
--

INSERT INTO `tugas_2025_12` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Dewi', '2025-12-04', '18:00', 'Operator'),
(2, 'Dewi', '2025-12-09', '18:00', 'Kameramen'),
(3, 'Ata Surya', '2025-12-02', '18:00', 'Operator'),
(4, 'Orel', '2025-12-15', '18:00', 'Operator'),
(5, 'Orel', '2025-12-02', '18:00', 'Supervisor'),
(6, 'Asha', '2025-12-15', '18:00', 'Supervisor'),
(7, 'There', '2025-12-31', '18:00', 'Operator'),
(8, 'Noel', '2025-12-07', '19:00', 'Supervisor'),
(9, 'Noel', '2025-12-21', '19:00', 'Supervisor'),
(10, 'Noel', '2025-12-28', '19:00', 'Supervisor'),
(11, 'Asha', '2025-12-02', '18:00', 'Kameramen'),
(12, 'Panji', '2025-12-21', '10:00', 'Supervisor'),
(13, 'There', '2025-12-14', '10:00', 'Operator'),
(14, 'Panji', '2025-12-21', '17:00', 'Operator'),
(15, 'Panji', '2025-12-21', '08:00', 'Supervisor'),
(16, 'Tita', '2025-12-07', '10:00', 'Operator'),
(17, 'Stella', '2025-12-07', '10:00', 'Kameramen'),
(18, 'Reva', '2025-12-07', '08:00', 'Kameramen'),
(19, 'Dhani', '2025-12-07', '08:00', 'Operator'),
(20, 'Dhani', '2025-12-14', '08:00', 'Kameramen'),
(21, 'Reva', '2025-12-14', '08:00', 'Operator'),
(22, 'Dhani', '2025-12-21', '10:00', 'Operator'),
(23, 'Reva', '2025-12-21', '10:00', 'Kameramen'),
(24, 'Tita', '2025-12-17', '18:00', 'Kameramen'),
(25, 'Stella', '2025-12-17', '18:00', 'Operator'),
(26, 'Weka', '2025-12-04', '18:00', 'Supervisor'),
(27, 'Weka', '2025-12-05', '18:00', 'Operator'),
(28, 'Weka', '2025-12-03', '18:00', 'Operator'),
(29, 'Vio', '2025-12-06', '18:00', 'Operator'),
(30, 'Vio', '2025-12-13', '18:00', 'Supervisor'),
(31, 'Christoforus Tadeus', '2025-12-07', '10:00', 'Supervisor'),
(32, 'Ata Surya', '2025-12-03', '18:00', 'Supervisor'),
(33, 'Lisa', '2025-12-09', '18:00', 'Operator'),
(34, 'Belinda', '2025-12-15', '18:00', 'Kameramen'),
(35, 'Aura', '2025-12-09', '18:00', 'Supervisor'),
(36, 'Belinda', '2025-12-17', '18:00', 'Supervisor'),
(37, 'Belinda', '2025-12-18', '18:00', 'Supervisor'),
(38, 'Tyas', '2025-12-18', '18:00', 'Operator'),
(39, 'Claire', '2025-12-07', '08:00', 'Supervisor'),
(40, 'Arya', '2025-12-07', '19:00', 'Operator'),
(41, 'Tyas', '2025-12-20', '18:00', 'Kameramen'),
(42, 'Evan', '2025-12-07', '19:00', 'Kameramen'),
(43, 'Claire', '2025-12-03', '18:00', 'Kameramen'),
(44, 'Claire', '2025-12-04', '18:00', 'Kameramen'),
(45, 'Chessa', '2025-12-07', '17:00', 'Operator'),
(46, 'Chessa', '2025-12-14', '10:00', 'Kameramen'),
(47, 'Chessa', '2025-12-20', '18:00', 'Operator'),
(48, 'Tyas', '2025-12-07', '17:00', 'Kameramen'),
(49, 'Egi', '2025-12-05', '18:00', 'Kameramen'),
(50, 'Egi', '2025-12-10', '18:00', 'Operator'),
(51, 'Rossa', '2025-12-16', '18:00', 'Operator'),
(52, 'Egi', '2025-12-16', '18:00', 'Kameramen'),
(53, 'Christoforus Tadeus', '2025-12-05', '18:00', 'Supervisor'),
(54, 'Aruna', '2025-12-12', '18:00', 'Kameramen'),
(55, 'Luciana Tyas', '2025-12-12', '18:00', 'Operator'),
(56, 'Aruna', '2025-12-10', '18:00', 'Kameramen'),
(57, 'Kane', '2025-12-14', '17:00', 'Operator'),
(58, 'Kane', '2025-12-06', '18:00', 'Kameramen'),
(59, 'Luciana Tyas', '2025-12-14', '10:00', 'Supervisor'),
(60, 'Bian', '2025-12-06', '18:00', 'Supervisor'),
(61, 'Bian', '2025-12-14', '17:00', 'Supervisor'),
(62, 'Kane', '2025-12-01', '18:00', 'Operator'),
(63, 'Kanes', '2025-12-18', '18:00', 'Kameramen'),
(64, 'Arya', '2025-12-13', '18:00', 'Kameramen'),
(65, 'Arya', '2025-12-14', '17:00', 'Kameramen'),
(66, 'Michel', '2025-12-11', '18:00', 'Operator'),
(67, 'Michel', '2025-12-19', '18:00', 'Operator'),
(68, 'Michel', '2025-12-08', '18:00', 'Supervisor'),
(69, 'Bian', '2025-12-01', '18:00', 'Supervisor'),
(70, 'Evan', '2025-12-01', '18:00', 'Kameramen'),
(71, 'Chris', '2025-12-07', '17:00', 'Supervisor'),
(72, 'Chris', '2025-12-08', '18:00', 'Kameramen'),
(73, 'Chris', '2025-12-10', '18:00', 'Supervisor'),
(74, 'Aurel', '2025-12-16', '18:00', 'Supervisor'),
(75, 'Vio', '2025-12-20', '18:00', 'Supervisor'),
(76, 'Callista', '2025-12-08', '18:00', 'Operator'),
(77, 'Callista', '2025-12-22', '18:00', 'Kameramen'),
(78, 'Callista', '2025-12-23', '18:00', 'Kameramen'),
(79, 'Ketrin', '2025-12-14', '19:00', 'Supervisor'),
(80, 'Aruna', '2025-12-14', '08:00', 'Supervisor'),
(81, 'Aurel', '2025-12-11', '18:00', 'Kameramen'),
(82, 'Jose', '2025-12-11', '18:00', 'Supervisor'),
(83, 'Jose', '2025-12-23', '18:00', 'Supervisor'),
(84, 'Nadia', '2025-12-31', '18:00', 'Supervisor'),
(85, 'Kanes', '2025-12-21', '08:00', 'Kameramen'),
(86, 'Nadia', '2025-12-26', '18:00', 'Supervisor'),
(87, 'Jose', '2025-12-26', '18:00', 'Kameramen'),
(88, 'Botun', '2025-12-12', '18:00', 'Supervisor'),
(89, 'Botun', '2025-12-13', '18:00', 'Operator'),
(90, 'Dewi', '2025-12-14', '19:00', 'Operator'),
(91, 'Deva', '2025-12-14', '19:00', 'Kameramen'),
(92, 'Jeni', '2025-12-21', '17:00', 'Kameramen'),
(93, 'Aura', '2025-12-28', '19:00', 'Operator'),
(94, 'Aura', '2025-12-23', '18:00', 'Operator'),
(95, 'Floren', '2025-12-19', '18:00', 'Kameramen'),
(96, 'Floren', '2025-12-21', '19:00', 'Kameramen'),
(97, 'Paul', '2025-12-21', '17:00', 'Supervisor'),
(98, 'Deva', '2025-12-31', '18:00', 'Kameramen'),
(99, 'Deva', '2025-12-28', '19:00', 'Kameramen'),
(100, 'Aurel', '2025-12-22', '18:00', 'Supervisor'),
(101, 'Luciana Tyas', '2025-12-21', '08:00', 'Operator'),
(102, 'Nawung', '2025-12-28', '10:00', 'Supervisor'),
(103, 'Pria', '2025-12-28', '10:00', 'Kameramen'),
(104, 'Pria', '2025-12-30', '18:00', 'Supervisor'),
(105, 'Toto', '2025-12-19', '18:00', 'Supervisor'),
(106, 'Ifa', '2025-12-28', '10:00', 'Operator'),
(107, 'Aoki', '2025-12-21', '19:00', 'Operator'),
(108, 'Aoki', '2025-12-22', '18:00', 'Operator'),
(109, 'Aoki', '2025-12-30', '18:00', 'Kameramen'),
(110, 'There', '2025-12-30', '18:00', 'Operator'),
(111, 'Lisa', '2025-12-29', '18:00', 'Operator'),
(112, 'Paul', '2025-12-27', '18:00', 'Supervisor'),
(113, 'Evan', '2025-12-26', '18:00', 'Operator'),
(114, 'Evan', '2025-12-28', '17:00', 'Kameramen'),
(115, 'Evan', '2025-12-28', '08:00', 'Supervisor'),
(116, 'Evan', '2025-12-28', '08:00', 'Operator'),
(117, 'Lisa', '2025-12-27', '18:00', 'Kameramen'),
(118, 'Bima', '2025-12-29', '18:00', 'Supervisor'),
(119, 'Toto', '2025-12-28', '17:00', 'Supervisor'),
(120, 'Tyas', '2025-12-28', '17:00', 'Operator'),
(121, 'Rikha', '2025-12-28', '08:00', 'Kameramen');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2026_01`
--

CREATE TABLE `tugas_2026_01` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2026_01`
--

INSERT INTO `tugas_2026_01` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Panji', '2026-01-04', '10:00', 'Supervisor'),
(2, 'Panji', '2026-01-04', '17:00', 'Supervisor'),
(3, 'Panji', '2026-01-04', '19:00', 'Supervisor'),
(4, 'Reva', '2026-01-03', '18:00', 'Operator'),
(5, 'Reva', '2026-01-10', '18:00', 'Kameramen'),
(6, 'Reva', '2026-01-04', '10:00', 'Kameramen'),
(7, 'Dhani', '2026-01-03', '18:00', 'Kameramen'),
(8, 'Dhani', '2026-01-10', '18:00', 'Operator'),
(9, 'Dhani', '2026-01-04', '10:00', 'Operator'),
(10, 'Noel', '2026-01-11', '19:00', 'Supervisor'),
(11, 'Noel', '2026-01-18', '19:00', 'Supervisor'),
(12, 'Noel', '2026-01-25', '19:00', 'Supervisor'),
(13, 'Aoki', '2026-01-04', '17:00', 'Kameramen'),
(14, 'Aoki', '2026-01-12', '18:00', 'Operator'),
(15, 'Aoki', '2026-01-20', '18:00', 'Operator'),
(16, 'Ifa', '2026-01-25', '08:00', 'Operator'),
(17, 'Tyas', '2026-01-06', '18:00', 'Operator'),
(18, 'Belinda', '2026-01-06', '18:00', 'Supervisor'),
(19, 'Belinda', '2026-01-08', '18:00', 'Operator'),
(20, 'Tyas', '2026-01-08', '18:00', 'Kameramen'),
(21, 'Belinda', '2026-01-13', '18:00', 'Supervisor'),
(22, 'Tyas', '2026-01-13', '18:00', 'Operator'),
(23, 'Jeni', '2026-01-04', '08:00', 'Kameramen'),
(24, 'Jeni', '2026-01-11', '08:00', 'Operator'),
(25, 'Jeni', '2026-01-18', '08:00', 'Kameramen'),
(26, 'Vio', '2026-01-17', '18:00', 'Operator'),
(27, 'Vio', '2026-01-24', '18:00', 'Operator'),
(28, 'Vio', '2026-01-09', '18:00', 'Operator'),
(29, 'Kane', '2026-01-18', '08:00', 'Operator'),
(30, 'Kane', '2026-01-25', '08:00', 'Kameramen'),
(31, 'Kane', '2026-01-31', '18:00', 'Operator'),
(32, 'Dewi', '2026-01-14', '18:00', 'Operator'),
(33, 'Dewi', '2026-01-15', '18:00', 'Supervisor'),
(34, 'Dewi', '2026-01-19', '18:00', 'Operator'),
(35, 'Evan', '2026-01-05', '18:00', 'Kameramen'),
(36, 'Evan', '2026-01-07', '18:00', 'Operator'),
(37, 'Rikha', '2026-01-04', '08:00', 'Operator'),
(38, 'Rikha', '2026-01-11', '08:00', 'Kameramen'),
(39, 'Rikha', '2026-01-18', '08:00', 'Supervisor'),
(40, 'Evan', '2026-01-09', '18:00', 'Kameramen'),
(41, 'Bian', '2026-01-31', '18:00', 'Supervisor'),
(42, 'Bian', '2026-01-25', '08:00', 'Supervisor'),
(43, 'Bian', '2026-01-07', '18:00', 'Supervisor'),
(44, 'Aurel', '2026-01-14', '18:00', 'Kameramen'),
(45, 'Paul', '2026-01-02', '18:00', 'Supervisor'),
(46, 'Paul', '2026-01-03', '18:00', 'Supervisor'),
(47, 'Floren', '2026-01-04', '19:00', 'Operator'),
(48, 'Floren', '2026-01-11', '19:00', 'Kameramen'),
(49, 'Ifa', '2026-01-12', '18:00', 'Supervisor'),
(50, 'Aurel', '2026-01-19', '18:00', 'Kameramen'),
(51, 'Callista', '2026-01-18', '10:00', 'Operator'),
(52, 'Callista', '2026-01-23', '18:00', 'Kameramen'),
(53, 'Callista', '2026-01-28', '18:00', 'Operator'),
(54, 'Pria', '2026-01-10', '18:00', 'Supervisor'),
(55, 'Stella', '2026-01-18', '10:00', 'Kameramen'),
(56, 'Stella', '2026-01-06', '18:00', 'Kameramen'),
(57, 'Stella', '2026-01-23', '18:00', 'Operator'),
(58, 'Asha', '2026-01-13', '18:00', 'Kameramen'),
(59, 'Asha', '2026-01-21', '18:00', 'Supervisor'),
(60, 'Christoforus Tadeus', '2026-01-05', '18:00', 'Supervisor'),
(61, 'Tita', '2026-01-11', '17:00', 'Operator'),
(62, 'Tita', '2026-01-18', '17:00', 'Operator'),
(63, 'Tita', '2026-01-25', '17:00', 'Kameramen'),
(64, 'Rossa', '2026-01-11', '17:00', 'Supervisor'),
(65, 'Rossa', '2026-01-18', '17:00', 'Supervisor'),
(66, 'Rossa', '2026-01-25', '17:00', 'Operator'),
(67, 'Weka', '2026-01-02', '18:00', 'Operator'),
(68, 'Weka', '2026-01-05', '18:00', 'Operator'),
(69, 'Arya', '2026-01-04', '19:00', 'Kameramen'),
(70, 'Aurel', '2026-01-12', '18:00', 'Kameramen'),
(71, 'Regio', '2026-01-14', '18:00', 'Supervisor'),
(72, 'Regio', '2026-01-18', '19:00', 'Operator'),
(73, 'Regio', '2026-01-22', '18:00', 'Supervisor'),
(74, 'Regio', '2026-01-27', '18:00', 'Supervisor'),
(75, 'Florencia', '2026-01-28', '18:00', 'Supervisor'),
(76, 'Arya', '2026-01-11', '17:00', 'Kameramen'),
(77, 'Arya', '2026-01-15', '18:00', 'Kameramen'),
(78, 'Aruna', '2026-01-21', '18:00', 'Kameramen'),
(79, 'Aruna', '2026-01-26', '18:00', 'Kameramen'),
(80, 'Aruna', '2026-01-29', '18:00', 'Kameramen'),
(81, 'Claire', '2026-01-08', '18:00', 'Supervisor'),
(82, 'Claire', '2026-01-19', '18:00', 'Supervisor'),
(83, 'Claire', '2026-01-20', '18:00', 'Supervisor'),
(84, 'Tyas', '2026-01-22', '18:00', 'Kameramen'),
(85, 'Luciana Tyas', '2026-01-21', '18:00', 'Operator'),
(86, 'Luciana Tyas', '2026-01-26', '18:00', 'Operator'),
(87, 'Tyas', '2026-01-18', '19:00', 'Kameramen'),
(88, 'Aura', '2026-01-11', '19:00', 'Operator'),
(89, 'Aura', '2026-01-25', '19:00', 'Operator'),
(90, 'Aura', '2026-01-17', '18:00', 'Kameramen'),
(91, 'Nadia', '2026-01-27', '18:00', 'Kameramen'),
(92, 'Nadia', '2026-01-17', '18:00', 'Supervisor'),
(93, 'There', '2026-01-04', '17:00', 'Operator'),
(94, 'There', '2026-01-01', '18:00', 'Operator'),
(95, 'Rosel', '2026-01-18', '17:00', 'Kameramen'),
(96, 'Rosel', '2026-01-25', '19:00', 'Kameramen'),
(97, 'Nawung', '2026-01-25', '10:00', 'Kameramen'),
(98, 'Orel', '2026-01-09', '18:00', 'Supervisor'),
(99, 'Orel', '2026-01-30', '18:00', 'Kameramen'),
(100, 'Tyas', '2026-01-01', '18:00', 'Kameramen'),
(101, 'There', '2026-01-15', '18:00', 'Operator'),
(102, 'Pria', '2026-01-25', '10:00', 'Supervisor'),
(103, 'Weka', '2026-01-01', '18:00', 'Supervisor'),
(104, 'Christoforus Tadeus', '2026-01-27', '18:00', 'Operator'),
(105, 'Christoforus Tadeus', '2026-01-02', '18:00', 'Kameramen'),
(106, 'Wima', '2026-01-30', '18:00', 'Operator'),
(107, 'Lisa', '2026-01-25', '10:00', 'Operator'),
(108, 'Lisa', '2026-01-30', '18:00', 'Supervisor'),
(109, 'Lisa', '2026-01-07', '18:00', 'Kameramen'),
(110, 'Nadia', '2026-01-24', '18:00', 'Kameramen'),
(111, 'Lisa', '2026-01-24', '18:00', 'Supervisor'),
(112, 'Luciana Tyas', '2026-01-29', '18:00', 'Operator'),
(113, 'Kanes', '2026-01-25', '17:00', 'Supervisor'),
(114, 'Orel', '2026-01-16', '18:00', 'Kameramen'),
(115, 'Asha', '2026-01-16', '18:00', 'Operator'),
(116, 'Wima', '2026-01-16', '18:00', 'Supervisor'),
(117, 'Chris', '2026-01-31', '18:00', 'Kameramen'),
(118, 'Chris', '2026-01-28', '18:00', 'Kameramen'),
(119, 'rieanaditya', '2026-01-26', '18:00', 'Supervisor'),
(120, 'There', '2026-01-23', '18:00', 'Supervisor'),
(121, 'rieanaditya', '2026-01-29', '18:00', 'Supervisor'),
(122, 'Deva', '2026-01-20', '18:00', 'Kameramen'),
(123, 'Naresh', '2026-01-22', '18:00', 'Operator');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2026_02`
--

CREATE TABLE `tugas_2026_02` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2026_02`
--

INSERT INTO `tugas_2026_02` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Reva', '2026-02-11', '18:00', 'Kameramen'),
(2, 'Dhani', '2026-02-11', '18:00', 'Operator'),
(3, 'Reva', '2026-02-12', '18:00', 'Operator'),
(4, 'Dhani', '2026-02-12', '18:00', 'Kameramen'),
(5, 'Reva', '2026-02-15', '10:00', 'Kameramen'),
(6, 'Dhani', '2026-02-15', '10:00', 'Operator'),
(7, 'Dewi', '2026-02-02', '18:00', 'Operator'),
(8, 'Dewi', '2026-02-04', '18:00', 'Supervisor'),
(9, 'Vio', '2026-02-07', '18:00', 'Operator'),
(10, 'Vio', '2026-02-14', '18:00', 'Operator'),
(11, 'Vio', '2026-02-21', '18:00', 'Operator'),
(12, 'Lisa', '2026-02-04', '18:00', 'Operator'),
(13, 'Lisa', '2026-02-09', '18:00', 'Operator'),
(14, 'Lisa', '2026-02-19', '18:00', 'Operator'),
(15, 'Jeni', '2026-02-01', '08:00', 'Kameramen'),
(16, 'Jeni', '2026-02-15', '08:00', 'Kameramen'),
(17, 'Jeni', '2026-02-08', '08:00', 'Operator'),
(18, 'Rikha', '2026-02-01', '08:00', 'Operator'),
(19, 'Rikha', '2026-02-08', '08:00', 'Kameramen'),
(20, 'Rikha', '2026-02-15', '08:00', 'Operator'),
(21, 'Orel', '2026-02-13', '18:00', 'Supervisor'),
(22, 'Chessa', '2026-02-01', '19:00', 'Kameramen'),
(23, 'Chessa', '2026-02-08', '10:00', 'Operator'),
(24, 'Chessa', '2026-02-22', '10:00', 'Operator'),
(25, 'Belinda', '2026-02-05', '18:00', 'Kameramen'),
(26, 'Belinda', '2026-02-10', '18:00', 'Supervisor'),
(27, 'Belinda', '2026-02-16', '18:00', 'Supervisor'),
(28, 'Tyas', '2026-02-05', '18:00', 'Operator'),
(29, 'Tyas', '2026-02-10', '18:00', 'Kameramen'),
(30, 'Tyas', '2026-02-16', '18:00', 'Operator'),
(31, 'Aoki', '2026-02-08', '10:00', 'Kameramen'),
(32, 'Aoki', '2026-02-22', '10:00', 'Kameramen'),
(33, 'Noel', '2026-02-01', '19:00', 'Supervisor'),
(34, 'Noel', '2026-02-08', '19:00', 'Supervisor'),
(35, 'Noel', '2026-02-22', '19:00', 'Supervisor'),
(36, 'Paul', '2026-02-05', '18:00', 'Supervisor'),
(37, 'Aurel', '2026-02-09', '18:00', 'Kameramen'),
(38, 'Aruna', '2026-02-25', '18:00', 'Kameramen'),
(39, 'Luciana Tyas', '2026-02-25', '18:00', 'Operator'),
(40, 'Luciana Tyas', '2026-02-20', '18:00', 'Operator'),
(41, 'Luciana Tyas', '2026-02-22', '08:00', 'Operator'),
(42, 'Aruna', '2026-02-20', '18:00', 'Kameramen'),
(43, 'Aruna', '2026-02-22', '08:00', 'Kameramen'),
(44, 'Tyas', '2026-02-01', '19:00', 'Operator'),
(45, 'Aura', '2026-02-10', '18:00', 'Operator'),
(46, 'Deva', '2026-02-02', '18:00', 'Supervisor'),
(47, 'Deva', '2026-02-04', '18:00', 'Kameramen'),
(48, 'Deva', '2026-02-09', '18:00', 'Supervisor'),
(49, 'Pria', '2026-02-01', '08:00', 'Supervisor'),
(50, 'Stella', '2026-02-19', '18:00', 'Kameramen'),
(51, 'Pria', '2026-02-15', '17:00', 'Supervisor'),
(52, 'There', '2026-02-22', '10:00', 'Supervisor'),
(53, 'Stella', '2026-02-22', '17:00', 'Kameramen'),
(54, 'Tita', '2026-02-22', '17:00', 'Supervisor'),
(55, 'Rossa', '2026-02-22', '17:00', 'Operator'),
(56, 'Weka', '2026-02-02', '18:00', 'Kameramen'),
(57, 'Tita', '2026-02-08', '17:00', 'Kameramen'),
(58, 'Tita', '2026-02-15', '17:00', 'Operator'),
(59, 'Rossa', '2026-02-08', '17:00', 'Operator'),
(60, 'Rossa', '2026-02-15', '17:00', 'Kameramen'),
(61, 'Kane', '2026-02-27', '18:00', 'Operator'),
(62, 'Kane', '2026-02-24', '18:00', 'Operator'),
(63, 'Kane', '2026-02-01', '10:00', 'Operator'),
(64, 'Nadia', '2026-02-19', '18:00', 'Supervisor'),
(65, 'Aura', '2026-02-17', '18:00', 'Supervisor'),
(66, 'Bian', '2026-02-27', '18:00', 'Supervisor'),
(67, 'Bian', '2026-02-01', '10:00', 'Supervisor'),
(68, 'Nadia', '2026-02-17', '18:00', 'Operator'),
(69, 'Christoforus Tadeus', '2026-02-03', '18:00', 'Supervisor'),
(70, 'Christoforus Tadeus', '2026-02-24', '18:00', 'Supervisor'),
(71, 'Jose', '2026-02-18', '18:00', 'Supervisor'),
(72, 'Jose', '2026-02-11', '18:00', 'Supervisor'),
(73, 'Arya', '2026-02-07', '18:00', 'Kameramen'),
(74, 'Arya', '2026-02-08', '19:00', 'Kameramen'),
(75, 'Arya', '2026-02-22', '19:00', 'Kameramen'),
(76, 'Stella', '2026-02-18', '18:00', 'Operator'),
(77, 'Callista', '2026-02-18', '18:00', 'Kameramen'),
(78, 'Callista', '2026-02-12', '18:00', 'Supervisor'),
(79, 'Floren', '2026-02-03', '18:00', 'Operator'),
(80, 'Aura', '2026-02-23', '18:00', 'Supervisor'),
(81, 'Nadia', '2026-02-23', '18:00', 'Operator'),
(82, 'Claire', '2026-02-08', '17:00', 'Supervisor'),
(83, 'Claire', '2026-02-08', '08:00', 'Supervisor'),
(84, 'Claire', '2026-02-08', '10:00', 'Supervisor'),
(85, 'Evan', '2026-02-01', '10:00', 'Kameramen'),
(86, 'Aura', '2026-02-26', '18:00', 'Operator'),
(87, 'Asha', '2026-02-03', '18:00', 'Kameramen'),
(88, 'Asha', '2026-02-15', '19:00', 'Operator'),
(89, 'Ketrin', '2026-02-21', '18:00', 'Supervisor'),
(90, 'Jeje', '2026-02-15', '19:00', 'Supervisor'),
(91, 'There', '2026-02-01', '17:00', 'Operator'),
(92, 'Kanes', '2026-02-26', '18:00', 'Kameramen'),
(93, 'Evan', '2026-02-22', '19:00', 'Operator'),
(94, 'Satrio', '2026-02-06', '18:00', 'Kameramen'),
(95, 'Satrio', '2026-02-13', '18:00', 'Kameramen'),
(96, 'Panji', '2026-02-01', '17:00', 'Supervisor'),
(97, 'Panji', '2026-02-07', '18:00', 'Supervisor'),
(98, 'Panji', '2026-02-08', '19:00', 'Operator'),
(99, 'Nawung', '2026-02-15', '10:00', 'Supervisor'),
(100, 'Naresh', '2026-02-28', '18:00', 'Operator'),
(101, 'Naresh', '2026-02-23', '18:00', 'Kameramen'),
(102, 'Naresh', '2026-02-14', '18:00', 'Supervisor'),
(103, 'Chris', '2026-02-17', '18:00', 'Kameramen'),
(104, 'Chris', '2026-02-24', '18:00', 'Kameramen'),
(105, 'Evan', '2026-02-27', '18:00', 'Kameramen'),
(106, 'Callista', '2026-02-13', '18:00', 'Operator'),
(107, 'Tyas', '2026-02-15', '19:00', 'Kameramen'),
(108, 'Tyas', '2026-02-21', '18:00', 'Kameramen'),
(109, 'Tyas', '2026-02-28', '18:00', 'Kameramen'),
(110, 'Orel', '2026-02-25', '18:00', 'Supervisor'),
(111, 'Christoforus Tadeus', '2026-02-06', '18:00', 'Supervisor'),
(112, 'Ata Surya', '2026-02-06', '18:00', 'Operator'),
(113, 'Ifa', '2026-02-15', '08:00', 'Supervisor'),
(114, 'Ifa', '2026-02-28', '18:00', 'Supervisor'),
(115, 'Deva', '2026-02-16', '18:00', 'Kameramen'),
(116, 'Rafael', '2026-02-22', '08:00', 'Supervisor'),
(117, 'Rafael', '2026-02-20', '18:00', 'Supervisor'),
(118, 'Chessa', '2026-02-14', '18:00', 'Kameramen');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2026_03`
--

CREATE TABLE `tugas_2026_03` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2026_03`
--

INSERT INTO `tugas_2026_03` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Jeni', '2026-03-08', '08:00', 'Operator'),
(2, 'Panji', '2026-03-01', '10:00', 'Kameramen'),
(3, 'Panji', '2026-03-01', '17:00', 'Supervisor'),
(4, 'Panji', '2026-03-01', '19:00', 'Operator'),
(5, 'Dewi', '2026-03-07', '18:00', 'Operator'),
(6, 'Dewi', '2026-03-14', '18:00', 'Operator'),
(7, 'Reva', '2026-03-15', '10:00', 'Kameramen'),
(8, 'Dhani', '2026-03-15', '10:00', 'Operator'),
(9, 'Aoki', '2026-03-08', '10:00', 'Kameramen'),
(10, 'Aoki', '2026-03-22', '10:00', 'Kameramen'),
(11, 'Egi', '2026-03-01', '17:00', 'Operator'),
(12, 'Chessa', '2026-03-01', '17:00', 'Kameramen'),
(13, 'Chessa', '2026-03-08', '10:00', 'Operator'),
(14, 'Chessa', '2026-03-15', '19:00', 'Kameramen'),
(15, 'Aoki', '2026-03-15', '17:00', 'Operator'),
(16, 'Egi', '2026-03-15', '19:00', 'Operator'),
(17, 'Tyas', '2026-03-08', '10:00', 'Supervisor'),
(18, 'Tyas', '2026-03-15', '17:00', 'Kameramen'),
(19, 'Chessa', '2026-03-22', '10:00', 'Supervisor'),
(20, 'Tyas', '2026-03-15', '19:00', 'Supervisor'),
(21, 'Tyas', '2026-03-22', '10:00', 'Operator'),
(22, 'Evan', '2026-03-02', '18:00', 'Kameramen'),
(23, 'Evan', '2026-03-03', '18:00', 'Operator'),
(24, 'Evan', '2026-03-04', '18:00', 'Kameramen'),
(25, 'Bian', '2026-03-22', '17:00', 'Supervisor'),
(26, 'Bian', '2026-03-08', '17:00', 'Supervisor'),
(27, 'Bian', '2026-03-28', '18:00', 'Operator'),
(28, 'There', '2026-03-01', '10:00', 'Operator'),
(29, 'Christoforus Tadeus', '2026-03-24', '18:00', 'Supervisor'),
(30, 'Belinda', '2026-03-17', '18:00', 'Supervisor'),
(31, 'Belinda', '2026-03-19', '18:00', 'Kameramen'),
(32, 'Belinda', '2026-03-23', '18:00', 'Supervisor'),
(33, 'Tyas', '2026-03-19', '18:00', 'Operator'),
(34, 'Tyas', '2026-03-23', '18:00', 'Kameramen'),
(35, 'Dhani', '2026-03-01', '19:00', 'Kameramen'),
(36, 'Dhani', '2026-03-08', '17:00', 'Operator'),
(37, 'Stella', '2026-03-17', '18:00', 'Kameramen'),
(38, 'Stella', '2026-03-15', '17:00', 'Supervisor'),
(39, 'Tyas', '2026-03-17', '18:00', 'Operator'),
(40, 'Stella', '2026-03-26', '18:00', 'Operator'),
(41, 'Callista', '2026-03-26', '18:00', 'Kameramen'),
(42, 'Rossa', '2026-03-23', '18:00', 'Operator'),
(43, 'Jeni', '2026-03-01', '08:00', 'Kameramen'),
(44, 'Jeni', '2026-03-15', '08:00', 'Kameramen'),
(45, 'Vio', '2026-03-21', '18:00', 'Operator'),
(46, 'Vio', '2026-03-28', '18:00', 'Supervisor'),
(47, 'Tita', '2026-03-22', '17:00', 'Operator'),
(48, 'Vio', '2026-03-14', '18:00', 'Supervisor'),
(49, 'There', '2026-03-21', '18:00', 'Supervisor'),
(50, 'Callista', '2026-03-21', '18:00', 'Kameramen'),
(51, 'Rossa', '2026-03-22', '17:00', 'Kameramen'),
(52, 'Arya', '2026-03-07', '18:00', 'Kameramen'),
(53, 'Rikha', '2026-03-01', '08:00', 'Operator'),
(54, 'Rikha', '2026-03-08', '08:00', 'Kameramen'),
(55, 'Rikha', '2026-03-15', '08:00', 'Operator'),
(56, 'Aruna', '2026-03-09', '18:00', 'Kameramen'),
(57, 'Aruna', '2026-03-18', '18:00', 'Operator'),
(58, 'Aruna', '2026-03-24', '18:00', 'Kameramen'),
(59, 'Arya', '2026-03-08', '17:00', 'Kameramen'),
(60, 'Christoforus Tadeus', '2026-03-05', '18:00', 'Supervisor'),
(61, 'Luciana Tyas', '2026-03-09', '18:00', 'Operator'),
(62, 'Luciana Tyas', '2026-03-18', '18:00', 'Supervisor'),
(63, 'Luciana Tyas', '2026-03-24', '18:00', 'Operator'),
(64, 'Arya', '2026-03-22', '19:00', 'Kameramen'),
(65, 'Ifa', '2026-03-08', '08:00', 'Supervisor'),
(66, 'Ifa', '2026-03-15', '08:00', 'Supervisor'),
(67, 'Claire', '2026-03-08', '19:00', 'Supervisor'),
(68, 'Claire', '2026-03-04', '18:00', 'Supervisor'),
(69, 'Claire', '2026-03-09', '18:00', 'Supervisor'),
(70, 'Tyas', '2026-03-01', '08:00', 'Supervisor'),
(71, 'Bian', '2026-03-04', '18:00', 'Operator'),
(72, 'Noel', '2026-03-01', '19:00', 'Supervisor'),
(73, 'Ketrin', '2026-03-01', '10:00', 'Supervisor'),
(74, 'Asha', '2026-03-08', '19:00', 'Kameramen'),
(75, 'Aurel', '2026-03-18', '18:00', 'Kameramen'),
(76, 'Asha', '2026-03-11', '18:00', 'Supervisor'),
(77, 'Dewi', '2026-03-22', '19:00', 'Supervisor'),
(78, 'Aurel', '2026-03-11', '18:00', 'Kameramen'),
(79, 'Rossa', '2026-03-11', '18:00', 'Operator'),
(80, 'Kanes', '2026-03-03', '18:00', 'Kameramen'),
(81, 'Jose', '2026-03-03', '18:00', 'Supervisor'),
(82, 'Lisa', '2026-03-02', '18:00', 'Operator'),
(83, 'Nawung', '2026-03-15', '10:00', 'Supervisor'),
(84, 'Chris', '2026-03-05', '18:00', 'Operator'),
(85, 'Chris', '2026-03-07', '18:00', 'Supervisor'),
(86, 'Kane', '2026-03-05', '18:00', 'Kameramen'),
(87, 'Kane', '2026-03-16', '18:00', 'Operator'),
(88, 'Kane', '2026-03-13', '18:00', 'Operator'),
(89, 'Aura', '2026-03-19', '18:00', 'Supervisor'),
(90, 'Weka', '2026-03-16', '18:00', 'Supervisor'),
(91, 'Pria', '2026-03-29', '19:00', 'Supervisor'),
(92, 'Pria', '2026-03-14', '18:00', 'Kameramen'),
(93, 'Nadia', '2026-03-30', '18:00', 'Supervisor'),
(94, 'Nadia', '2026-03-31', '18:00', 'Operator'),
(95, 'Lisa', '2026-03-30', '18:00', 'Operator'),
(96, 'Lisa', '2026-03-31', '18:00', 'Supervisor'),
(97, 'Tyas', '2026-03-22', '19:00', 'Operator'),
(98, 'Florencia', '2026-03-20', '18:00', 'Supervisor'),
(99, 'Orel', '2026-03-10', '18:00', 'Operator'),
(100, 'Aura', '2026-03-27', '18:00', 'Operator'),
(101, 'Orel', '2026-03-16', '18:00', 'Kameramen'),
(102, 'Kanes', '2026-03-10', '18:00', 'Supervisor'),
(103, 'Deva', '2026-03-10', '18:00', 'Kameramen'),
(104, 'Deva', '2026-03-29', '17:00', 'Operator'),
(105, 'Deva', '2026-03-22', '08:00', 'Kameramen'),
(106, 'Alta', '2026-03-20', '18:00', 'Kameramen'),
(107, 'Ketrin', '2026-03-13', '18:00', 'Kameramen'),
(108, 'Deva', '2026-03-27', '18:00', 'Supervisor'),
(109, 'Naresh', '2026-03-25', '18:00', 'Operator'),
(110, 'Naresh', '2026-03-29', '10:00', 'Operator'),
(111, 'Naresh', '2026-03-30', '18:00', 'Kameramen'),
(112, 'Christoforus Tadeus', '2026-03-12', '18:00', 'Supervisor'),
(113, 'Aura', '2026-03-25', '18:00', 'Supervisor'),
(114, 'Asha', '2026-03-12', '18:00', 'Operator'),
(115, 'Paul', '2026-03-12', '18:00', 'Kameramen'),
(116, 'Rafael', '2026-03-13', '18:00', 'Supervisor'),
(117, 'Toto', '2026-03-22', '08:00', 'Supervisor'),
(118, 'Alta', '2026-03-22', '08:00', 'Operator'),
(119, 'Florencia', '2026-03-25', '18:00', 'Kameramen'),
(120, 'Jose', '2026-03-20', '18:00', 'Operator'),
(121, 'Rafael', '2026-03-31', '18:00', 'Kameramen'),
(122, 'Tyas', '2026-03-27', '18:00', 'Kameramen'),
(123, 'Tyas', '2026-03-26', '18:00', 'Supervisor');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2026_04`
--

CREATE TABLE `tugas_2026_04` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2026_04`
--

INSERT INTO `tugas_2026_04` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Ifa', '2026-04-26', '17:00', 'Operator'),
(2, 'Ifa', '2026-04-26', '19:00', 'Supervisor'),
(3, 'Ifa', '2026-04-19', '17:00', 'Operator'),
(4, 'Panji', '2026-04-12', '10:00', 'Supervisor'),
(5, 'Panji', '2026-04-12', '17:00', 'Supervisor'),
(6, 'Panji', '2026-04-12', '19:00', 'Supervisor'),
(7, 'Dewi', '2026-04-12', '19:00', 'Operator'),
(8, 'Dewi', '2026-04-19', '17:00', 'Supervisor'),
(9, 'Chessa', '2026-04-12', '10:00', 'Operator'),
(10, 'Chessa', '2026-04-26', '17:00', 'Kameramen'),
(11, 'Aoki', '2026-04-12', '10:00', 'Kameramen'),
(12, 'Aoki', '2026-04-26', '17:00', 'Supervisor'),
(13, 'Egi', '2026-04-19', '19:00', 'Kameramen'),
(14, 'Chessa', '2026-04-19', '19:00', 'Operator'),
(15, 'Claire', '2026-04-15', '18:00', 'Supervisor'),
(16, 'Claire', '2026-04-16', '18:00', 'Supervisor'),
(17, 'Dewi', '2026-04-01', '18:00', 'Operator'),
(18, 'Dewi', '2026-04-26', '19:00', 'Kameramen'),
(19, 'There', '2026-04-19', '19:00', 'Supervisor'),
(20, 'There', '2026-04-12', '17:00', 'Operator'),
(21, 'Stella', '2026-04-13', '18:00', 'Kameramen'),
(22, 'Belinda', '2026-04-14', '18:00', 'Supervisor'),
(23, 'Belinda', '2026-04-21', '18:00', 'Kameramen'),
(24, 'Tyas', '2026-04-14', '18:00', 'Kameramen'),
(25, 'Tyas', '2026-04-21', '18:00', 'Operator'),
(26, 'Tyas', '2026-04-13', '18:00', 'Operator'),
(27, 'Aruna', '2026-04-15', '18:00', 'Kameramen'),
(28, 'Aruna', '2026-04-19', '08:00', 'Kameramen'),
(29, 'Luciana Tyas', '2026-04-15', '18:00', 'Operator'),
(30, 'Luciana Tyas', '2026-04-19', '08:00', 'Operator'),
(31, 'Tyas', '2026-04-01', '18:00', 'Kameramen'),
(32, 'Aurel', '2026-04-27', '18:00', 'Kameramen'),
(33, 'Deva', '2026-04-12', '19:00', 'Kameramen'),
(34, 'Deva', '2026-04-13', '18:00', 'Supervisor'),
(35, 'Deva', '2026-04-14', '18:00', 'Operator'),
(36, 'Lisa', '2026-04-08', '18:00', 'Operator'),
(37, 'Lisa', '2026-04-22', '18:00', 'Operator'),
(38, 'Vio', '2026-04-11', '18:00', 'Supervisor'),
(39, 'Vio', '2026-04-18', '18:00', 'Operator'),
(40, 'Pria', '2026-04-25', '18:00', 'Supervisor'),
(41, 'Nawung', '2026-04-19', '10:00', 'Supervisor'),
(42, 'Aura', '2026-04-23', '18:00', 'Operator'),
(43, 'Nawung', '2026-04-26', '10:00', 'Kameramen'),
(44, 'Asha', '2026-04-08', '18:00', 'Supervisor'),
(45, 'Botun', '2026-04-08', '18:00', 'Kameramen'),
(46, 'Botun', '2026-04-09', '18:00', 'Supervisor'),
(47, 'Asha', '2026-04-16', '18:00', 'Operator'),
(48, 'Evan', '2026-04-12', '17:00', 'Kameramen'),
(49, 'Evan', '2026-04-11', '18:00', 'Kameramen'),
(50, 'Bian', '2026-04-11', '18:00', 'Operator'),
(51, 'Rossa', '2026-04-27', '18:00', 'Operator'),
(52, 'Jose', '2026-04-23', '18:00', 'Supervisor'),
(53, 'Jose', '2026-04-27', '18:00', 'Supervisor'),
(54, 'Bian', '2026-04-17', '18:00', 'Supervisor'),
(55, 'Jeni', '2026-04-12', '08:00', 'Operator'),
(56, 'Rossa', '2026-04-26', '10:00', 'Supervisor'),
(57, 'Noel', '2026-04-05', '19:00', 'Supervisor'),
(58, 'Naresh', '2026-04-05', '19:00', 'Operator'),
(59, 'Tita', '2026-04-26', '10:00', 'Operator'),
(60, 'Naresh', '2026-04-19', '10:00', 'Kameramen'),
(61, 'Rossa', '2026-04-19', '10:00', 'Operator'),
(62, 'Tita', '2026-04-29', '18:00', 'Operator'),
(63, 'Aura', '2026-04-28', '18:00', 'Operator'),
(64, 'Rikha', '2026-04-12', '08:00', 'Kameramen'),
(65, 'Dhani', '2026-04-24', '18:00', 'Supervisor'),
(66, 'Reva', '2026-04-24', '18:00', 'Operator'),
(67, 'Dhani', '2026-04-26', '08:00', 'Supervisor'),
(68, 'Reva', '2026-04-26', '08:00', 'Operator'),
(69, 'Orel', '2026-04-17', '18:00', 'Kameramen'),
(70, 'Orel', '2026-04-16', '18:00', 'Kameramen'),
(71, 'Floren', '2026-04-18', '18:00', 'Kameramen'),
(72, 'Floren', '2026-04-20', '18:00', 'Operator'),
(73, 'Floren', '2026-04-23', '18:00', 'Kameramen'),
(74, 'Kanes', '2026-04-19', '17:00', 'Kameramen'),
(75, 'Tyas', '2026-04-26', '19:00', 'Operator'),
(76, 'Christoforus Tadeus', '2026-04-21', '18:00', 'Supervisor'),
(77, 'Pria', '2026-04-06', '18:00', 'Supervisor'),
(78, 'Paul', '2026-04-07', '18:00', 'Supervisor'),
(79, 'Paul', '2026-04-09', '18:00', 'Operator'),
(80, 'Florencia', '2026-04-29', '18:00', 'Supervisor'),
(81, 'Florencia', '2026-04-22', '18:00', 'Supervisor'),
(82, 'Kanes', '2026-04-20', '18:00', 'Kameramen'),
(83, 'Jeni', '2026-04-25', '18:00', 'Kameramen'),
(84, 'Rikha', '2026-04-25', '18:00', 'Operator'),
(85, 'Stella', '2026-04-29', '18:00', 'Kameramen'),
(86, 'Ketrin', '2026-04-09', '18:00', 'Kameramen'),
(87, 'Kane', '2026-04-26', '08:00', 'Kameramen'),
(88, 'Kane', '2026-04-17', '18:00', 'Operator'),
(89, 'Egi', '2026-04-22', '18:00', 'Kameramen'),
(90, 'Tyas', '2026-04-07', '18:00', 'Operator'),
(91, 'Tyas', '2026-04-10', '18:00', 'Operator'),
(92, 'Christoforus Tadeus', '2026-04-07', '18:00', 'Kameramen'),
(93, 'Chris', '2026-04-10', '18:00', 'Supervisor'),
(94, 'Chris', '2026-04-30', '18:00', 'Operator'),
(95, 'Weka', '2026-04-12', '08:00', 'Supervisor'),
(96, 'Naresh', '2026-04-28', '18:00', 'Supervisor'),
(97, 'Noel', '2026-04-30', '18:00', 'Kameramen'),
(98, 'Naresh', '2026-04-30', '18:00', 'Supervisor'),
(99, 'Jeni', '2026-04-19', '08:00', 'Supervisor'),
(100, 'Deva', '2026-04-18', '18:00', 'Supervisor'),
(101, 'Tyas', '2026-04-28', '18:00', 'Kameramen'),
(102, 'There', '2026-04-24', '18:00', 'Kameramen');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_2026_05`
--

CREATE TABLE `tugas_2026_05` (
  `id` int(11) NOT NULL,
  `username` varchar(150) DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `position` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `tugas_2026_05`
--

INSERT INTO `tugas_2026_05` (`id`, `username`, `date`, `time`, `position`) VALUES
(1, 'Dhani', '2026-05-03', '08:00', 'Supervisor'),
(2, 'Dhani', '2026-05-03', '10:00', 'Supervisor'),
(3, 'Reva', '2026-05-03', '08:00', 'Operator'),
(4, 'Reva', '2026-05-03', '10:00', 'Operator'),
(5, 'Dhani', '2026-05-03', '17:00', 'Supervisor'),
(6, 'Reva', '2026-05-03', '17:00', 'Operator'),
(7, 'Kane', '2026-05-10', '08:00', 'Operator'),
(8, 'Kane', '2026-05-17', '08:00', 'Operator'),
(9, 'Bian', '2026-05-10', '08:00', 'Supervisor'),
(10, 'Bian', '2026-05-17', '08:00', 'Supervisor'),
(11, 'Vio', '2026-05-23', '18:00', 'Operator'),
(12, 'Vio', '2026-05-16', '18:00', 'Supervisor'),
(13, 'Evan', '2026-05-03', '08:00', 'Kameramen'),
(14, 'Evan', '2026-05-10', '10:00', 'Kameramen'),
(15, 'Chessa', '2026-05-17', '10:00', 'Kameramen'),
(16, 'Egi', '2026-05-17', '10:00', 'Operator'),
(17, 'Chessa', '2026-05-10', '19:00', 'Operator'),
(18, 'Chessa', '2026-05-24', '10:00', 'Kameramen'),
(19, 'Chessa', '2026-05-31', '10:00', 'Operator'),
(20, 'Lisa', '2026-05-11', '18:00', 'Operator'),
(21, 'Lisa', '2026-05-12', '18:00', 'Operator'),
(22, 'Stella', '2026-05-12', '18:00', 'Kameramen'),
(23, 'Tyas', '2026-05-10', '19:00', 'Kameramen'),
(24, 'Tyas', '2026-05-24', '10:00', 'Operator');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_form`
--

CREATE TABLE `tugas_form` (
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
  `expires_at` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_form_audit`
--

CREATE TABLE `tugas_form_audit` (
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
  `created_at` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `tugas_form_slot`
--

CREATE TABLE `tugas_form_slot` (
  `id` int(11) NOT NULL,
  `form_id` int(11) NOT NULL,
  `date` varchar(50) NOT NULL,
  `time` varchar(50) NOT NULL,
  `operator_username` varchar(150) DEFAULT NULL,
  `kameramen_username` varchar(150) DEFAULT NULL,
  `supervisor_username` varchar(150) DEFAULT NULL,
  `updated_at` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `youtube_embeds`
--

CREATE TABLE `youtube_embeds` (
  `id` varchar(100) NOT NULL,
  `url` varchar(255) NOT NULL,
  `order_index` int(11) DEFAULT 0,
  `is_visible` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `youtube_embeds`
--

INSERT INTO `youtube_embeds` (`id`, `url`, `order_index`, `is_visible`) VALUES
('yt-1777497207553', 'https://youtu.be/7y3AlFqobck?si=HoSKCZdrYLbPr3PB', 2, 1),
('yt-1777497242761', 'https://youtu.be/tPIDedX3zQ4?si=VHukpSDtC64xZ49s', 1, 1),
('yt-1777497264044', 'https://youtu.be/PWkkMvsp4Ws?si=SvjcHAqsgWNJ3518', 3, 1),
('yt-1777504238859', 'https://youtu.be/d5mZ5SKWIx4?si=uguT4CisV_sxs6la', 4, 1);

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `anggota`
--
ALTER TABLE `anggota`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uniq_anggota_username` (`username`);

--
-- Indeks untuk tabel `carousel_slides`
--
ALTER TABLE `carousel_slides`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `google_maps_embed`
--
ALTER TABLE `google_maps_embed`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `instagram_posts`
--
ALTER TABLE `instagram_posts`
  ADD PRIMARY KEY (`id_instagram`);

--
-- Indeks untuk tabel `kegiatan`
--
ALTER TABLE `kegiatan`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `kegiatan_form`
--
ALTER TABLE `kegiatan_form`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uniq_kegiatan_form_slug` (`slug`);

--
-- Indeks untuk tabel `news`
--
ALTER TABLE `news`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `slug` (`slug`);

--
-- Indeks untuk tabel `news_categories`
--
ALTER TABLE `news_categories`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD UNIQUE KEY `slug` (`slug`);

--
-- Indeks untuk tabel `news_category_mapping`
--
ALTER TABLE `news_category_mapping`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_news_category` (`news_id`,`category_id`),
  ADD KEY `category_id` (`category_id`);

--
-- Indeks untuk tabel `organization_profiles`
--
ALTER TABLE `organization_profiles`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `sertifikat_config`
--
ALTER TABLE `sertifikat_config`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tentang_crembo_config`
--
ALTER TABLE `tentang_crembo_config`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tentang_crembo_media`
--
ALTER TABLE `tentang_crembo_media`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2025_05`
--
ALTER TABLE `tugas_2025_05`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2025_06`
--
ALTER TABLE `tugas_2025_06`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2025_07`
--
ALTER TABLE `tugas_2025_07`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2025_08`
--
ALTER TABLE `tugas_2025_08`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2025_09`
--
ALTER TABLE `tugas_2025_09`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2025_10`
--
ALTER TABLE `tugas_2025_10`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2025_11`
--
ALTER TABLE `tugas_2025_11`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2025_12`
--
ALTER TABLE `tugas_2025_12`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2026_01`
--
ALTER TABLE `tugas_2026_01`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2026_02`
--
ALTER TABLE `tugas_2026_02`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2026_03`
--
ALTER TABLE `tugas_2026_03`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2026_04`
--
ALTER TABLE `tugas_2026_04`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_2026_05`
--
ALTER TABLE `tugas_2026_05`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_form`
--
ALTER TABLE `tugas_form`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uniq_tugas_form_slug` (`slug`);

--
-- Indeks untuk tabel `tugas_form_audit`
--
ALTER TABLE `tugas_form_audit`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tugas_form_slot`
--
ALTER TABLE `tugas_form_slot`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uniq_tugas_form_slot` (`form_id`,`date`,`time`);

--
-- Indeks untuk tabel `youtube_embeds`
--
ALTER TABLE `youtube_embeds`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `news_category_mapping`
--
ALTER TABLE `news_category_mapping`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT untuk tabel `sertifikat_config`
--
ALTER TABLE `sertifikat_config`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT untuk tabel `tentang_crembo_config`
--
ALTER TABLE `tentang_crembo_config`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `news_category_mapping`
--
ALTER TABLE `news_category_mapping`
  ADD CONSTRAINT `news_category_mapping_ibfk_1` FOREIGN KEY (`news_id`) REFERENCES `news` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `news_category_mapping_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `news_categories` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
