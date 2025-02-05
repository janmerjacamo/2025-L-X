-- disable bac payment provider
UPDATE payment_provider
   SET bac_key_id = NULL,
       bac_key_text = NULL;
