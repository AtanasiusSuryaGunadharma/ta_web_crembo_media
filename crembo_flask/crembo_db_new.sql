-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 29 Apr 2026 pada 16.56
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
  `status_akun` varchar(20) NOT NULL DEFAULT 'aktif'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `anggota`
--

INSERT INTO `anggota` (`id`, `nama`, `username`, `telp`, `password`, `role`, `tgl_lahir`, `email`, `alamat`, `status_akun`) VALUES
(1, 'FX Harso Susanto', 'Babe', '+6285772732906', 'scrypt:32768:8:1$JyBWrrkOGuhe7jTd$54a802bcc99d80b72fd817a2e48f375e5ca0b60c4b17b9122e94bf8dbfeae146e509440f31c3a14e9ad60ba48f92b985f6ecc43b2f47a4b62af5cb3cf23fca08', 'admin', '1970-08-20', 'suksisnarf@gmail.com', NULL, 'aktif'),
(2, 'Nico Gandawijaya', 'Niko', '082134997990', 'scrypt:32768:8:1$ko6WHg49UtiRs2dG$f5679cc0164f379e1eb6fd61be4e43dc6303bc9b4019893422296fd3c0737e82eab49f24542a03c982804f00299f9b9378e524cece687f91c3e93fe0948dce6b', 'admin', NULL, NULL, NULL, 'aktif'),
(3, 'Christoforus Tadeus', 'Christoforus Tadeus', '085894525162', 'scrypt:32768:8:1$fSixa3Z12Exd4P0g$77ceac2f30d86b53d3149988a50272238460b0d29b5648b567fb8571ca8fe811d55ffadb3739dc2ffdc1379439f43f0ab34181ababb6698f465fd9a12332f4ec', 'admin', NULL, NULL, NULL, 'aktif'),
(4, 'Riean Aditya', 'rieanaditya', '0895336757747', 'scrypt:32768:8:1$8FnTsAy3hjS6C622$32131dc844eb221136fa21134940d2b2452cf1e1e65af209404300ad95c71bb339b4fadb5e902e9b99fbf0304e652c9c50cc64b98d4e461ff28399f4d6ebdb40', 'admin', NULL, NULL, NULL, 'aktif'),
(5, 'Katherine Ivana Hadi', 'Ketrin', '081386618220', 'scrypt:32768:8:1$kocjdDopnrgca8lt$83958b6ec208ca1facc17f762955dcd7f8285181930e43c16ceb506e11e9f1c0c957e7b0f7c3960a4f88b04ac5916e3cc16d9473455ffba02b9bf927cf9f89a4', 'admin', NULL, NULL, NULL, 'aktif'),
(6, 'Pria', 'Pria', '081228330226', 'scrypt:32768:8:1$4nCgWeSwWR7cEYj3$d40e423b6ec59c153bfc0843476c48bcbffdcfe69844e4a9e942320107b0c624c3a68c1cb0a597bdbba85a117cbfbd0b3be743cb18abb77365a621a6f63c7eee', 'admin', '2026-04-29', 'pria@gmail.com', 'Jl Baciro', 'aktif'),
(7, 'Aurel', 'Aurel', '085878495255', 'scrypt:32768:8:1$WsEELS5C525TKDKr$d70c89e1f0e8c98944a9b9a56e4927f19805d4ed92a319da6f7e6743884392281825a9298587241f07fc4af871e6013771f9a07471d79bff4df7ede78c44b0bd', 'user', NULL, NULL, NULL, 'aktif'),
(8, 'Dewi', 'Dewi', '087700652865', 'scrypt:32768:8:1$z8mtUa3kB43bDHfP$5f8d2ff4647348ed2fc60b4eeaa8e027c892a1e2500cf4015554a2940367dbfa0d48a9d3c5b121e2ea6472abbdd2ea5e073e0bd7bcfe58b9e1ec62032813e80d', 'admin', NULL, NULL, NULL, 'aktif'),
(9, 'Febrian', 'Febrian', '081220239158', 'scrypt:32768:8:1$v7BBX2N2uKgzq8gu$245b6a3723e1ddd0d0b3178c685448a8d792bd42d7ebd52d4ba423cfb89a5c9a85612c260f5f396a4e1a0b3cd4901605c6e06537a4f5622d83fb3fccd24f6e4a', 'user', NULL, NULL, NULL, 'aktif'),
(10, 'Lisa', 'Lisa', '081327428922', 'scrypt:32768:8:1$zugzoG5d10AkzMMw$e01ff24899ee0f31c5aed313b7dce55a82d8888eee6144a6c42087df37cf413053eadd69a80cf63af2a6cce7fd4a154450c13c95eb7785029519285b3f467b93', 'user', NULL, NULL, NULL, 'aktif'),
(11, 'Rosel', 'Rosel', '081919811671', 'scrypt:32768:8:1$O1LLlNyMX3bRjTBo$0029c8759982f8bcbb82dcfa08f7011c6683bc2dc6bae201959d90d8eb480131023d34cd9c022ecfb497b20a0b8ca63ba44e47641d08633bfcc66f10a18f4221', 'user', NULL, NULL, NULL, 'aktif'),
(12, 'Vio', 'Vio', '085866168513', 'scrypt:32768:8:1$MQB3DJzR55lAxfRz$4e1c6da0f56406b6ff7fd39004e2a0e72a61d12e990ad4bb03aa6b47e74d3ec16e71eaf69541ee638d8d53079db24544ae5da0762b8545b0a92bdfc95ee84aef', 'user', NULL, NULL, NULL, 'aktif'),
(13, 'Vista', 'Vista', '085876328357', 'scrypt:32768:8:1$VhoXIsf5sBBRQnej$91cab4e2d24456956e6c5dd96d0856b91c364c019fae6538f81f6477292350f7c63c9f7f393f40fe639bf379f0ca8624837b8ebf5add04050c4f2d07dd2495b4', 'user', NULL, NULL, NULL, 'aktif'),
(14, 'Weka', 'Weka', '081327129511', 'scrypt:32768:8:1$X9L6HCXHYkOsnz7A$e10cad76e595424543b19ef0129860197d76c593ea713839805b46e03027e25e7f80bf50d3cb2c5245209f9ebbd0d3eea8a9c141e82161f50557413c8e3bf0ac', 'admin', '2009-09-09', 'wekawijaya044@gmail.com', NULL, 'aktif'),
(15, 'Wima', 'Wima', '089508852626', 'scrypt:32768:8:1$DkrEKgzzK58KDWRJ$22c21297aadeaf6c23a71851f6f0b1fdceafc3cab46c3f64efc135d3f057835eb22c33aaf01793e649cc71d444436edd32676cc1c8da5699894fd03e6c3a2bd4', 'user', NULL, NULL, NULL, 'aktif'),
(16, 'Nawung', 'Nawung', '081228680603', 'scrypt:32768:8:1$8eC2MkZma35ywHMU$883da4c68fb22452c790379a3d27d3213c8d08bd0984dbe900ecc0d843f7a8c50ec342c0bb29e56d82ae537c267b82c071cd4bd7f702798845d88133d7644cf9', 'user', NULL, NULL, NULL, 'aktif'),
(17, 'Panji', 'Panji', '089677330106', 'scrypt:32768:8:1$E62Rv9BJW0qyjSdV$a15df746db84de526237ed4597d310d6aecec556024877a2ef0bfcf847a45ec4e9942ae4abda89e3c56aa0469721393cfabfb4a37dce0d98b403dc1020869934', 'user', NULL, NULL, NULL, 'aktif'),
(18, 'Yuta', 'Yuta', '085602917625', 'scrypt:32768:8:1$aRKL0gXhh4swWOYH$17feeca47d7286fb51d169dda8f755eb6e42145bb184deaeae0ed314cb14fd83edaeb675c71ec7ba506f7b68954ed85aa5eebbad32fefabdb6bcde3a32b278b6', 'user', NULL, NULL, NULL, 'aktif'),
(19, 'Shehan', 'Shehan', '087878836187', 'scrypt:32768:8:1$oyUllzXRah1PHjZ8$266f06fb807d46674aba4a1d54733bdd385971eac547a54bb518f206dc98bcd32b59670a59019467fdf912cab1ccf4f85c05177d84ee3ed83dbf197e4d2838a9', 'admin', NULL, NULL, NULL, 'aktif'),
(20, 'Asha', 'Asha', '081226402137', 'scrypt:32768:8:1$fEMSfKPrYGs77Bf5$6c4bf03bafdf6a39cdf6ec3a58f0715ea71714fcfb97bc464d5beb45a078e40d5a5a7eed6294a760af4b1a63de52d67319501ba3ecca44a4e5ca24827f0c9d51', 'user', NULL, NULL, NULL, 'aktif'),
(21, 'Aura', 'Aura', '088215905899', 'scrypt:32768:8:1$8RCaZofpMtIEDQVP$1f5bdac57f12d3c4d49c8db23148b3145da7cca697173c796a2d342174b9da9f275207ce6fedff60f8c8dac3ffe0a6ac63c4ed88cc08f7a2d1e9327416ee3e1e', 'user', NULL, NULL, NULL, 'aktif'),
(22, 'Belinda', 'Belinda', '083146801642', 'scrypt:32768:8:1$9qd2Zy3VegtCGFHn$d14fafb239f6f3e8bf0dd862471ad6b2e3070af2abbd67c2439498bbff64ad003e894fc1e7cf5f475273c379aa8f8fd2d5dfb0ff13b2ae7c1f8d695ef4babe9f', 'user', NULL, NULL, NULL, 'aktif'),
(23, 'Bian', 'Bian', '089694800055', 'scrypt:32768:8:1$spGXHMjT3MUWjBH7$4ff3d50e25265020283510214ef615c8eb56d557c37f372eb2d52e01adf26b900f3d8b9c4c050139945f812e3bff6dc6dd6a5953ae6924031fccf390e1c460c0', 'user', NULL, NULL, NULL, 'aktif'),
(24, 'Bima', 'Bima', '0818112847', 'scrypt:32768:8:1$ixgFvPKkDANWB4SG$718405ff79ae853f5c6ed7b42084621ce7b292b40c095b44a78e6ece1a4e83abed472fb9c046b9328f3dd3fe7c0b3b1f7c452b8f9514ddf03b598f0186019aef', 'user', NULL, NULL, NULL, 'aktif'),
(25, 'Botun', 'Botun', '081378591744', 'scrypt:32768:8:1$y8nOtt5q4HXUWnrP$f2a763bb9640d9a69405a0cf52c9b1814520f404cd62acb7568e4d0a60c6bd7d153f803278d2326e95e1d0e14df82152ecd2a270ab984e07976784ad29c28f4c', 'user', NULL, NULL, NULL, 'aktif'),
(26, 'Claire', 'Claire', '082224063848', 'scrypt:32768:8:1$WJhJwJZ8lwOVke4o$e47392ac968708a21ab949c555cd2bb6ebede6468e27bc1e17313a2c5ae1488a7072a0882c06a0436e1ee162d82d77c1059d4879444fde6863f536815ee18ebd', 'user', NULL, NULL, NULL, 'aktif'),
(27, 'Florencia', 'Florencia', '081329017910', 'scrypt:32768:8:1$qksHCQRkvMPAO9h1$0437f83eb6de474ffc8ca4d6056137ee20a281c4774424b71da9c9e824ba93041792c010e3473152b7881823f9e06788aa3a7f0c5763032e092416d5d6054b8e', 'user', '2010-07-07', 'vlflorencialidya@gmail.com', NULL, 'aktif'),
(28, 'Ifa', 'Ifa', '0882007217238', 'scrypt:32768:8:1$LnEWLueSEc2uz3Bt$15cb6dff047fa026f131bf92b79539aacf01707f07c401b2ff355053ccd2f7705faa32d6dd80eb9f8775a51743af126bc2dd11100250d143117800eedc579e46', 'user', NULL, NULL, NULL, 'aktif'),
(29, 'Jeni', 'Jeni', '085248994747', 'scrypt:32768:8:1$dies2yefonWdDRJm$055401c9134ca88d2d1191c02f0e91a6dafdd9b2564957ad1c6842b954e3e018791b04826a8794aae0155e6b4b9f46cf2a73d4332a534bfeecb4d28d2da8d2b5', 'user', NULL, NULL, NULL, 'aktif'),
(30, 'Jossefina', 'Jose', '0895321245610', 'scrypt:32768:8:1$TnitTZEy6j78SsFn$cea859177bafa0ec3e2499c60729dc5ad9fe6b18ef0155c8eadc13cf75822c2b09fbcc0d57b79c5c028ad0a97029440398d1feab7b5182fdb7ba66ea3cbf7f60', 'user', NULL, NULL, NULL, 'aktif'),
(31, 'Kanes', 'Kanes', '089675333345', 'scrypt:32768:8:1$jzhfgo7Sr1Lueftt$675a2469c4a4636c037565cb8b18b4586f88a98a81fefe979ff2e2ac27a57f3fb80af2b5a3b1024b5b8db0447f4961214fcf3604d3c39322a95283ef2ce826ab', 'user', NULL, NULL, NULL, 'aktif'),
(32, 'Kinan', 'Kinan', '081239902121', 'scrypt:32768:8:1$MiUAKrxwhsdO5gES$4736c7dbc71b0ed9acfb6cc1a45403afd6a3b31cd6e6e64909f4e525708be15b2c0edc3bf98197aae393b4c6f28c1b2eb1a3423a43e24b4d86f4341078acd9e8', 'user', NULL, NULL, NULL, 'aktif'),
(33, 'Veny', 'Veny', '082271499065', 'scrypt:32768:8:1$HTAwll6LRFjM3Jlo$a2f7cfde57033414d36b38fcbce69516dcad40ae02bc4e84d1367e877d9856c145210dcbf1af83733c77f2ad827f2327ac5cf045f65adb20bbd0adf1007c17a0', 'user', NULL, NULL, NULL, 'aktif'),
(34, 'Juven', 'Juven', '082247972976', 'scrypt:32768:8:1$hQ1x54n6LWot5VYV$a2ba1bf9b1c6babdf603fb99addb241900fd5604b314ee7c1c9751446da06b715d8cdf6d44671db9c8740dae9a52ba7ac3e47ab9a2cf14057cd0dd3d5ec77d0e', 'user', NULL, NULL, NULL, 'aktif'),
(35, 'Chris', 'Chris', '+62 812-1343-0315', 'scrypt:32768:8:1$R1dD1KBC9u9PKfNy$701279e4f400341c73b34290165e86e8879fbfb4a4daa9d59ccd734a84c7bbd80e5fed1f02ed18d0a4334ad46ab2b32dd56f7a3826d42087eff4a7828801e788', 'user', NULL, NULL, NULL, 'aktif'),
(36, 'Alta', 'Alta', '+62 812-2991-0550', 'scrypt:32768:8:1$z99rBAe6O6BmRrCg$ba572b8ef08c050dbcb7032417b2740f8ebb29efa76c91cada77c5cc225dfc65641d9cd4b57982a5fe0742d9daff02dd31875d51f7e336afdb1509dc4a65aab2', 'user', NULL, NULL, NULL, 'aktif'),
(37, 'Rikha', 'Rikha', '+62 812-5410-6511', 'scrypt:32768:8:1$qQh5HoIuf3oqRplz$5c332edd766cbed1b458d0d71f611c850d0a809d3ee5722af4183226a26141dc755eca74ca87b5e88d54fd27b9f14abc04d67d92e5d63ae6e2cd515e584d55cf', 'user', NULL, NULL, NULL, 'aktif'),
(38, 'Michell', 'Michel', '+62 817-7285-4812', 'scrypt:32768:8:1$ZYiCgWAD2KeMwFGq$ec99d80b98d65745df18255daedc79b4a4402e4285ff850549c8eba0cddf5f5096835bc882c127f55b9c91788c4c9b6d92875b050b07c17e21ea8819b2cfc632', 'user', NULL, NULL, NULL, 'aktif'),
(39, 'Michelle', 'Michelle', '+62 838-3802-5077', 'scrypt:32768:8:1$S7szxLHJBy7K7bLi$bd8bc8dbc11217c65eea78ded7c9912fb2f22801963bb5c20dc3a01a606f9c5c0c7c2c542dc06fa6873550af41fc882815e74dba5904a1f77d8ade5d80ac1fb0', 'user', NULL, NULL, NULL, 'aktif'),
(40, 'Naresh', 'Naresh', '+62 858-7927-1256', 'scrypt:32768:8:1$DQMapYNxMGqcRtHa$8143d5aca1985488b61a218bf23fdef3c267f10a714f012d6457f42d375aeef02fbd89f351c1925cf791cf0b00b47332d43dbd61837d2b1aabe6509943b7a237', 'user', NULL, NULL, NULL, 'aktif'),
(41, 'Nesto', 'Nesto', '+62 821-2276-0357', 'scrypt:32768:8:1$HvsT0YViHYwCn8Tn$00674242159227cf6dce2295513d9b74597154cd84f49498472029693112499dc2de14f2483761a05215d1ada40bbf8f8fb2303d0f92aa6483bd1854403c685b', 'user', NULL, NULL, NULL, 'aktif'),
(42, 'Noel', 'Noel', '+62 815-6826-1411', 'scrypt:32768:8:1$EIx5tRRMYa5ng11G$f8ba9a40a7fd536d48b95eeece57b5d47c7b2c23a9e0cf1b1b3336a1cbaf85640b140ff5c2e6e13732bf23c51efde894c881325ab25f95836bfdb74070becde7', 'user', NULL, NULL, NULL, 'aktif'),
(43, 'Paul', 'Paul', '+62 888-0268-6783', 'scrypt:32768:8:1$Yt2s6jWtsIww9QPC$74ed569487811366d290d02dedca99637f9dfec228d1170febc9a7ffe5144e1e4277a87025a784cc4b7d568428577b5dd3dad683df7246c8539b7f9f546e9a92', 'user', NULL, NULL, NULL, 'aktif'),
(44, 'Putra', 'Putra', '+62 822-4312-2313', 'scrypt:32768:8:1$RZFbloXwMMISgV5n$ffa25bee6f54a2f21d878e1a130af64a1a2595e65cb6e332af293498bc805bb40aa637f96b479b1448d8d101a97d6bba8e42e4d4095d4b44f53f6730cf63d354', 'user', NULL, NULL, NULL, 'aktif'),
(45, 'Rossa', 'Rossa', '+62 889-5799-655', 'scrypt:32768:8:1$eE7CHjhWnzrPs9Ww$27447c8f095aa919adb7a362197c2af08fcb253a425625c83864ea393d4e6a5250b071e98f69b1c008742f0a2e30038e797b5b8e62c8b3c24999f9a7c5750541', 'user', NULL, NULL, NULL, 'aktif'),
(46, 'Satrio', 'Satrio', '+62 888-0679-0315', 'scrypt:32768:8:1$XUE0q9zEL1gk1ytu$a0507f02d9c35223190dc17f018128fafd8ac6b94efb03cdb5377ed0e65d5f9608cd42f60de86855b01908476f1a0be82d68b2129cd33ec0f1a67b3609482b54', 'user', NULL, NULL, NULL, 'aktif'),
(47, 'There', 'There', '+62 878-9855-5370', 'scrypt:32768:8:1$IURMpb4BKozcqzQv$723f337692d6b0d53fb92fe0fe09155c782e20fd28efdde82b965db14ec9bc78672524ea4a751f681dd839f960a1e26a671051c4f37c31eea9338d5261bc7ef8', 'user', '2011-01-30', 'yoshefasabatini@gmail.com', NULL, 'aktif'),
(48, 'Toto', 'Toto', '+62 858-2013-4705', 'scrypt:32768:8:1$YJlFgQbsb2jXCukn$9d06995e524e5bd8a46383d786634a3a95974229cdaece7ac41411f3489dbec4185e71040493b5c072a7262d2bc724bfa781a8f5861f358ea29ba525b1b9b67d', 'user', NULL, NULL, NULL, 'aktif'),
(49, 'Tyas', 'Tyas', '+62 889-8582-6095', 'scrypt:32768:8:1$rbhGaMjTfmgzPkVY$6fa412ca61b11f8cb4530b5b25a32cf75e5770e99f0b741405a33ae139fbaa3414d9c9155f987bde4461cd3568f886fecdee0f02c4436e4b8ebaea7958304183', 'user', NULL, NULL, NULL, 'aktif'),
(50, 'Atanasius Surya', 'Ata Surya', '+62 813-5075-1753', 'scrypt:32768:8:1$s5gFKcBxeFbrwkNf$706b187bf8067913093a44e6f50d6c62bd63060dad321a8341eb99237443e2f9f2cd7afd31f8814abd28128fc8e1d51877149a2bfab49b40bf9b00c2eec700b7', 'super_admin', '2004-05-13', 'atanasiussurya@gmail.com', NULL, 'aktif'),
(51, 'Rafael', 'Rafael', '+62 813-9033-3758', 'scrypt:32768:8:1$XTjB22QBETTUwjPH$2a4f5f9da5660c3b8f94f928ea8e76ddebf18f576c1f36a5c526c01dd032081466edf3f2cb14ad766d1dc3820f5f763d18ae13d63bdae711d422759b31339168', 'user', NULL, NULL, NULL, 'aktif'),
(52, 'Frugal', 'Frugal', '+62 813-9830-7591', 'scrypt:32768:8:1$D03o2WrlrPCX74Bo$72cdb406fc98e86d38df12ce1c8a48663dc428ef7bb713c088fd8bf266b87db957219d003b0f939d6c82dfe5f7d6d3bf652a0a591caf0352b323a636e5505c7b', 'user', NULL, NULL, NULL, 'aktif'),
(53, 'Daflo', 'Daflo', '+62 821-5766-3661', 'scrypt:32768:8:1$qYu1t0PYcrvx7Ub6$4537820f12b8e4e212f818059949df3b7827aa82ce621327c48f49e0eda76aac09876c6a6ef8ad18d66df1dc31cf24fdaf3f38235e80501b173330c5c5709e70', 'user', NULL, NULL, NULL, 'aktif'),
(54, 'Orel', 'Orel', '+62 838-6564-6354', 'scrypt:32768:8:1$qs2s3KqRqZw1eETw$c9fcfd8727fe0cbfe0424bad9a58c4d5fc9e881d9152e37a39ba68d554468d566760eeb272b6c561419881f8e10fdf97b3370138fd5bb0fb06924a0389e13aaa', 'user', NULL, NULL, NULL, 'aktif'),
(55, 'Jeje', 'Jeje', '+62 851-7150-3299', 'scrypt:32768:8:1$vdKYr7PknsBZp06Q$c4f882227a43d10bb74b4e0b8add4d85cdc28b5f0272c701ac55ff48accb0f56c9fbb1a826c9e4cd3788585e2e896485617861a1dcf920749389ef54f8edb2cc', 'user', NULL, NULL, NULL, 'aktif'),
(56, 'Regio', 'Regio', '+62 878-7755-5879', 'scrypt:32768:8:1$nRWs4w7Hr0NeJanf$45cde6f342a36b065dbf5034882dd19e2d126fcec974ee093619ce7b02b67305fa341c390dc71deadc933744e239a75931956cd60be37d7c63923f73cbec511f', 'user', '2002-11-29', 'regionanda2@gmail.com', NULL, 'aktif'),
(57, 'Nadia', 'Nadia', '+62 857-9730-7843', 'scrypt:32768:8:1$5Y1pVLD71ql68qoU$2b7cb6ac920cb2ad2f5c82cbe7ed1ba32a23aedac03b273571ce4eca8930fd0643860920da68edc27ad7cc8b8b33044e6e7c111aae1f9d345af8876a9e9ba40d', 'user', NULL, NULL, NULL, 'aktif'),
(58, 'Tita', 'Tita', '+62 856-2423-6122', 'scrypt:32768:8:1$ThJvle16qAEZEXe9$4fcd81d7ab981e7c040c1df112ec5c51418f8c75ae13d3f3cee9c9b276f1d790eb993aad5dd70177f55f20e1ea9eb0f27cbea5feec48993c1e9f96278de0b612', 'user', NULL, NULL, NULL, 'aktif'),
(59, 'Floren', 'Floren', '+62 821-4693-7640', 'scrypt:32768:8:1$b03ee1H4ci0zSrVO$0c988d0ab6e82d2d8c1e60ba3c3cfa2919d44f6de8c135af5539ba6c92cd1366ae0b27a945a2f02d1a6a9881b2292bda319f5e4f902ff1ddcb324e9a2e3b5953', 'user', '2005-06-20', 'flojuni236@gmail.com', NULL, 'aktif'),
(60, 'Baladeva', 'Deva', '082286767108', 'scrypt:32768:8:1$96QCeigF8xsu8IZF$8d248c68043ea3b902c3c3b4821e0e6273328d60e94ede7c21bf45aeccf53f0e432dbb5c73eb6d09cc420048f329ea35ba83b031760eab09fe451c71afc68f6b', 'user', '', NULL, NULL, 'aktif'),
(61, 'Chessa', 'Chessa', '+62 878-8307-5397', 'scrypt:32768:8:1$ufUyCIhP6VEoLqtH$228d0ba6caa4e5cc15f633c1d697935a930bfb035a55f303522f0711ed980d06e052ecd64715d21ed171fd8f92b90975dca4a91ec9bb4f741aa36793634fed0e', 'user', '', 'krin3112@gmail.com', NULL, 'aktif'),
(65, 'Dhani', 'Dhani', '085868202008', 'scrypt:32768:8:1$c80fb04psPvyRhwK$ba5f9452efd6714223668efe346b886234747efbdadda641f89c6043ef7787693536bb397aed2d9ded0eeb7e85b79c59aec23c9c47291f60ff4924a7cab956cb', 'user', '', 'ardhani.ign@gmail.com', NULL, 'aktif'),
(66, 'Evan', 'Evan', '088239466566', 'scrypt:32768:8:1$rA0YHXLWixjOuBWo$e56e9267f006c0507aa23eafa0c29cabfcfbe53496316b2708b8aaa0d4b546ce3feb3f03fa3c9db6270a541ef9f8eae8d6096e2f1771c8333cb92423add6e127', 'user', '', 'evanpaskalis464@gmail.com', NULL, 'aktif'),
(67, 'Aruna', 'Aruna', '081973372901', 'scrypt:32768:8:1$vW6eHF8B4YJ6MbFs$c38dbfd05be7673a5064fe2c6799e2363b2b62ae6cf3c515b853ff2214f61854dfd4d6f0b7bfde77b7ba4a1c5b96e70cdb110562933a2f178378e70e5d67878d', 'user', '', 'arunayudyaw@gmail.com', NULL, 'aktif'),
(68, 'Egi', 'Egi', '087715815710', 'scrypt:32768:8:1$gMectZBAUXWHfN8J$37faf85dc311c2403705d21c74e4870a1b326596644421d61c2b76513e05e8516bc59841b4afb99b6fa20de33d808419f95449c932f965e1b519dca67a66a31d', 'user', '', 'regina.caelia18@gmail.com', NULL, 'aktif'),
(69, 'Reva', 'Reva', '082325249481', 'scrypt:32768:8:1$Nyn6g6Orn3h2grlg$f2de22fcf0501ffe227e9e14b8c5496d2a94625e0674f000207c05468db3c17a8e43f9a9894e744c87b63c58280b096b9040b7f0afb05115fa1d8710bd512a3b', 'user', '', 'lrevadewi@gmail.com', NULL, 'aktif'),
(70, 'Kane', 'Kane', '081919090631', 'scrypt:32768:8:1$dz0dJJxmAWSdkSia$fc492396568f1962d6455f0d19e92b53b224045af923a4fecb892447516425f8551343c92ce4f991f65fac0a34a331b31d56135dea9f1f7eae471bea3c135608', 'user', '', 'regina.kns17@gmail.com', NULL, 'aktif'),
(71, 'Stella', 'Stella', '089613983033', 'scrypt:32768:8:1$bXDQCOaFeT7rh4iN$771d95d2caf7280673b7e3e6fdeada15d35bc16986ab59ad5fad3a9a2c5b53f9ef9f0f9a6e7844f2bfda029d87f40bdeafc5174a8a45e4a4514415b14bedcb69', 'user', '', 'stellamaria758@gmail.com', NULL, 'aktif'),
(72, 'Arya', 'Arya', '081324859094', 'scrypt:32768:8:1$i611QYvOcmtTNXBt$8f443083de045a9d389a51e27a4ca5713296679e91c2203e870245b56d60ab016d1063f8587a14004cfc1cd9ce7e7cc323827bcb7c1300c9ea86a1e05d74a309', 'user', '', 'aryadwika2010@gmail.com', NULL, 'aktif'),
(73, 'Aoki', 'Aoki', '085743665416', 'scrypt:32768:8:1$uVLwUhPRoRMREi5O$401e7e9b5f793f89952b3845f87ebec60e64faff8655f816ef82541465a7a0e2b82b02aa00602ec61f6a75c939d2e528d671547a507b46c4f4b0629c752103b5', 'user', '', 'gizelleraina2401@gmail.com', NULL, 'aktif'),
(74, 'Luciana Tyas', 'Luciana Tyas', '0895630325989', 'scrypt:32768:8:1$G8tPh3OwDuLnwYYe$b75e000738a948ec413c8d092d2761b6cf1ba990c2f38b3686ecfb16b875dd5ba510348cab7f763fddbce1fdae2863829ad267dffc94d42c6aab89d15625f174', 'user', '', 'lucianaxaverinetyas@gmail.com', NULL, 'aktif'),
(75, 'Callista', 'Callista', '087836461101', 'scrypt:32768:8:1$Tx9b068Kbha1DNhD$7ed5c89ddd38db5955dc7d40ac96539c974f0197189167725b0f96828fb3d97437c1cd41981f42bc04b1636419e567f6f7f634695e7b2de25afc032ff6b98a96', 'user', '', 'lumodocalista@gmail.com', NULL, 'aktif');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `anggota`
--
ALTER TABLE `anggota`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uniq_anggota_username` (`username`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
\n
--
-- Struktur dari tabel 	entang_crembo_config
--

CREATE TABLE 	entang_crembo_config (
  id int(11) NOT NULL,
  description text DEFAULT NULL,
  utton_text varchar(255) DEFAULT NULL,
  utton_link varchar(255) DEFAULT NULL,
  uto_seconds int(11) DEFAULT 5
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel 	entang_crembo_config
--

INSERT INTO 	entang_crembo_config (id, description, utton_text, utton_link, uto_seconds) VALUES
(1, 'Ringkasan profil organisasi, visi pelayanan multimedia, serta peran Crembo dalam mendukung kegiatan liturgi dan agenda komunitas.', 'Pelajari Lebih Lanjut', 'profil.html', 5);

-- --------------------------------------------------------

--
-- Struktur dari tabel 	entang_crembo_media
--

CREATE TABLE 	entang_crembo_media (
  id varchar(100) NOT NULL,
  	ype varchar(50) DEFAULT 'image',
  url text DEFAULT NULL,
  order_index int(11) DEFAULT 0,
  is_visible tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
