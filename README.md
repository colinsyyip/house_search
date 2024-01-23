# House Search

Working project on retrieving information on available rentals in Leiden from the following sites:
* Room
* Funda
* Kamernet
* Pararius

Data retrieved using bare Python `requests` as well as Selenium and the classes that run/execute these queries can be run from CRON. Listing information stored in SQLite database for later retrieval/analysis. Some initial visualizations can be seen below.

![hist] (rent_distribution.png)

![lin_fit_general] (lin_fit_rent_area.png)

![lin_fit_by_nh] (lin_fit_rent_area_by_nh.png)

![lin_fit_by_nh_boxed] (lin_fit_rent_area_by_nh_boxed.png)
