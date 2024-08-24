select cron.schedule_in_database('GINESYS_AUTO_SETTLEMENT_JOB_SLPL','*/15 * * * *','call main.db_pro_auto_settle_unpost()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_DATA_SERVICE_2_SLPL','*/1 * * * *','call main.db_pro_gds2_event_enqueue()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_INVSTOCK_INTRA_LOG_AGG_SLPL','30 seconds','call main.invstock_intra_log_refresh()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_INVSTOCK_LOG_AGG_SLPL','30 seconds','call main.invstock_log_refresh()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_PERIOD_CLOSURE_JOB_SLPL','*/2 * * * *','call main.db_pro_period_closure_dequeue()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_POS_STLM_AUDIT_SLPL','*/5 * * * *','call main.db_pro_pos_stlm_audit()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_RECALCULATE_TAX_JOB_SLPL','*/30 * * * *','call main.db_pro_recalculategst()','STARTRON-PROD');

--CUBE

select cron.schedule_in_database('GINESYS_STOCK_BOOK_PIPELINE_DELTA_AGG_SLPL','*/5 * * * *','call db_pro_delta_agg_pipeline_stock()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_STOCK_BOOK_SUMMARY_DELTA_AGG_SLPL','*/5 * * * *','call db_pro_delta_agg_stock_book_summary()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_STOCK_BOOK_SUMMARY_COSTADJ_DELTA_AGG_SLPL','*/5 * * * *','call db_pro_delta_agg_stock_book_summary_costadj()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_STOCK_BOOK_SUMMARY_STOCKPOINTWISE_DELTA_AGG_SLPL','*/5 * * * *','call db_pro_delta_agg_stock_book_summary_stockpointwise()','STARTRON-PROD');

select cron.schedule_in_database('GINESYS_STOCK_BOOK_SUMMARY_BATCH_SERIAL_DELTA_AGG_SLPL','*/5 * * * *','call db_pro_delta_agg_stock_book_summary_batchwise()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_STOCK_BOOK_SUMMARY_COSTADJ_BATCH_SERIAL_DELTA_AGG_SLPL','*/5 * * * *','call db_pro_delta_agg_stock_book_summary_costadj_batchwise()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_STOCK_BOOK_SUMMARY_STOCKPOINT_BATCH_SERIAL_WISE_DELTA_AGG_SLPL','*/5 * * * *','call db_pro_delta_agg_stock_book_summary_stockpoint_batchwise()','STARTRON-PROD');

select cron.schedule_in_database('GINESYS_STK_AGEING_FIRSTTIME_SLPL','0 0 * * *','call db_pro_stk_ageing_firsttime()','STARTRON-PROD');
select cron.schedule_in_database('GINESYS_STK_AGEING_STKPOINTWISE_FIRSTTIME_SLPL','0 0 * * *','call db_pro_stk_ageing_stockpointwise_firsttime()','STARTRON-PROD');