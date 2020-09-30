
#Security

Setup-
  - Required Python 3.8.5 - Project created upon.
  - Create virtual environment - python3 -m venv <venv-name>
  - Install requirements.txt residing in security project directory.
  - Connect with database PostgreSQL suggested (project tested upon PostgreSQL 12.4).
  - Read ER Diagram residing in security project as er-diagram.png.
 
 
 
Project Structure -
```

└── portfolio  
    ├── __init__.py  
    ├── __pycache__  
    ├── migrations  
    │   ├── 0001_initial.py  
    │   ├── __init__.py  
    │   └── __pycache__  
    ├── templates  
    │   ├── error.html  
    │   ├── holding_list.html  
    │   ├── return_list.html  
    │   └── success.html 
    │   └── ticker_add_or_update.html 
    │   └── ticker_list.html 
    │   └── trade_add_or_update.html 
    │   └── trade_list.html 
    ├── admin.py  
    ├── apps.py  
    ├── models.py  
    ├── serializers.py  
    ├── tests.py  
    ├── urls.py  
    └── views.py 
    ├── README.md  
├── security  
│   ├── __init__.py  
│   ├── __pycache__  
│   ├── asgi.py  
│   ├── settings.py  
│   ├── urls.py  
│   ├── utils.py  
│   └── wsgi.py
├──.gitignore
├── manage.py 
├── Procfile
├── requirements.txt  

```

Assumptions and extras - 
  - Values for returns can be negative on Returns List page.
  - Price can be 0 for a trade
  - Holdings list is needed to be represented with avg_buy_price as computed or non-computed string (un-evaluated).
  - A trade cannot be added with Quantity less than the Quantity available (bought - sold) for a particular security/ticker.
