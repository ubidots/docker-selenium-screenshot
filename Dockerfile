FROM selenium/standalone-chrome
MAINTAINER Sebastian Saldarriaga <sebastian@ubidots.com>

# Install packages
RUN sudo apt-get update && \
    sudo apt-get install --no-install-recommends -y python3-pip apt-utils

# Install selenium & pyvirtualdisplay
RUN pip3 install selenium pyvirtualdisplay

# Copy python scripts
COPY src/selenium_screenshot.py selenium_screenshot.py

# Run script
ENTRYPOINT ["python3", "selenium_screenshot.py"]
