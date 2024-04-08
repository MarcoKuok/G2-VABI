# G2-VABI Project: Financial Statement Analysis Dashboard

## How to deploy the Plotly dashboard locally on your computer ✏

1. Clone this repository with Github Desktop or type the following command:
   ```bash
   git clone https://github.com/MarcoKuok/G2-VABI.git
   ```

2. Open VSCode/ Sublime Text and navigate to the folder where you cloned the repository
   
3. Run your terminal/ command prompt and type the following command:
   ```bash
   python -m pip install requirements.txt
   ```
   
4. After all dependencies are installed, run the following command:
   ```bash
   flask run
   ```
   
5. Copy the first URL shown on your terminal output, it should look something like this:
   ```bash
   * Running on all addresses (0.0.0.0)
   * Running on http://127.0.01:5000
   ```

6. You may visit the URL itself OR insert it into your Tableau Dashboard by adding it as a Web Object, paste the URL into the input field, and click 'OK'.
   
7. Enjoy playing around with the dashboard 😁
