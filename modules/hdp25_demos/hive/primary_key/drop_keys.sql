use tpch_bin_flat_orc_2;

alter table region drop constraint region_c1;
alter table nation drop constraint nation_c1;
alter table nation drop constraint nation_c2;
alter table part drop constraint part_c1;
alter table supplier drop constraint supplier_c1;
alter table supplier drop constraint supplier_c2;
alter table partsupp drop constraint partsupp_c1;
alter table customer drop constraint customer_c1;
alter table customer drop constraint customer_c2;
alter table lineitem drop constraint lineitem_c1;
alter table orders drop constraint orders_c1;
alter table partsupp drop constraint partsupp_c2;
alter table partsupp drop constraint partsupp_c3;
alter table orders drop constraint orders_c2;
alter table lineitem drop constraint lineitem_c2;
alter table lineitem drop constraint lineitem_c3;
