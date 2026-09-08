from doe_dap_dl import DAP

wdh = DAP('wdh.energy.gov')

wdh.setup_basic_auth()

wdh.download_orders(order_ids=["cc1565e94f4a4187afd7d0d7d"])


