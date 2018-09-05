-- schema.sql

drop database if exists awesome;

create database awesome;

use awesome;

grant select,insert,update,delete on awesome.* to 'root'@'admin_root' identified by 'root';

create table users(
	`id` varchar(50) not null,
	`email` varchar(50) not null,
	`passwd` varchar(50) not null,
	`admin` boolean not null,
	`name` varchar(50) not null,
	`image` varchar(500) not null,
	`create_dt` real not null,
	unique key `idx_email` (`email`),
	primary key (`id`),
	key `idx_create_dt` (`create_dt`)
)engine = innodb default charset = utf8;

create table blogs(
	`id` varchar(50) not null,
	`user_id` varchar(50) not null,
	`user_name` varchar(50) not null,
	`user_image` varchar(500) not null,
	`name` varchar(50) not null,
	`summary` varchar(200) not null,
	`content` mediumtext not null,
	`create_dt` real not null,
	key `idx_create_at` (`create_dt`),
	primary key (`id`)
)engine = innodb default charset=utf8;

create table comments(
	`id` varchar(50) not null,
	`blog_id` varchar(50) not null,
	`user_id` varchar(50) not null,
	`user_name` varchar(50) not null,
	`content` mediumtext not null,
	`create_dt` real not null,
	key `idx_create_dt` (`create_dt`),
	primary key (`id`)
)engine = innodb default charset = utf8;


