-- create database starbook with owner postgres;

-- 用户相关schema
create schema account;

-- 用户表

create table account.account
(
  id               serial               not null
    constraint account_pk primary key,
  nickname         varchar,
  avatar           varchar,
  school           varchar,
  gender           integer,
  student_identify boolean,
  sign_date        timestamp default now() not null,
  true_name        varchar,
  telephone        varchar,
  openid           varchar unique,
  self_note_count  integer default 0,
  self_cum_reading integer default 0,
  week_cum_reading integer default 0,
  contious_count  integer default 0
);

comment on column account.account.id is '用户id';
comment on column account.account.nickname is '昵称';
comment on column account.account.avatar is '头像链接';
comment on column account.account.school is '学校';
comment on column account.account.gender is '0-未知 1-男 2-女';
comment on column account.account.student_identify is '是否是学生';
comment on column account.account.sign_date is '注册日期';
comment on column account.account.telephone is '电话';
comment on column account.account.true_name is '真实姓名';
comment on column account.account.openid is 'QQ小程序的open_id';
comment on column account.account.self_note_count is '发表读书笔记数量';
comment on column account.account.self_cum_reading is '总阅读时长';
comment on column account.account.week_cum_reading is '周阅读时长';

alter table account.account owner to postgres;

create unique index account_id_uindex on account.account (id);

-- 用户喜欢表
create table account.account_likes
(
  id bigserial,
	uid integer,
	nid bigint,
  add_date timestamp default now(),
	constraint account_likes_pk
		primary key (uid, nid)
);

alter table account.account_likes owner to postgres;

-- 用户收藏表
create table account.account_favors
(
  id bigserial,
	uid integer,
	nid bigint,
  add_date timestamp default now(),
	constraint account_favors_pk
		unique (uid, nid)
);

alter table account.account_favors owner to postgres;



-- 榜单schema
create schema toplist

-- 总榜表

create table toplist.total_reading
(
  ranking  integer not null
    constraint total_reading_pk primary key,
  uid      integer,
  nickname varchar,
  avatar   varchar
);

comment on column toplist.total_reading.ranking is '排名';

alter table toplist.total_reading owner to postgres;

-- 周榜表

create table toplist.week_reading
(
  ranking  integer,
  uid      integer,
  nickname varchar,
  avatar   varchar
);

alter table toplist.week_reading owner to postgres;

-- 发帖记录schema
create schema records;

-- 读书笔记表

create table records.note
(
  uid            integer,
  nid            bigserial not null
    constraint note_pk
      primary key,
  book_name      varchar   not null,
  post_date      timestamp default now(),
  read_duration   integer,
  text_content   varchar,
  img_link       varchar default null,
  like_count     integer   default 0,
  favor_count integer   default 0,
  comment_count  integer   default 0
);

comment on column records.note.post_date is '本次阅读时长';
comment on column records.note.read_duration is '本次阅读时长（分钟）';
comment on column records.note.text_content is '笔记内容';
comment on column records.note.like_count is '本帖点赞总数';
comment on column records.note.favor_count is '本帖喜欢总数';
comment on column records.note.comment_count is '本帖评论总数';

alter table records.note owner to postgres;

create unique index note_nid_uindex on records.note (nid);

-- 笔记评论表

create table records.comment
(
	uid integer not null,
	nickname varchar not null,
	avatar varchar not null,
	nid bigint,
	cid bigserial not null
		constraint comment_pk
			primary key,
	text_content varchar,
	post_date timestamp default now(),
	school varchar
);

comment on column records.comment.text_content is '评论内容';

alter table records.comment owner to postgres;

create unique index comment_cid_uindex
	on records.comment (cid);




