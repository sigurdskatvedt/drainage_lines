# Use an official QGIS image
FROM qgis/qgis

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/
COPY .env /app/.env

# Remove the existing SAGA GIS version
RUN apt-get update && apt-get remove -y saga

# Install system dependencies for SAGA GIS and wxWidgets
# Note: Adjust 'jammy' to your specific Ubuntu release if necessary
RUN apt-get install -y --no-install-recommends software-properties-common gnupg \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 6856E1DB1AC82609 \
    && apt-add-repository 'deb https://repos.codelite.org/wx3.2/ubuntu/ jammy universe' \
    && apt-get update && apt-get install -y \
    libwxgtk3.0-gtk3-dev libtiff5-dev libgdal-dev libproj-dev \
    libexpat1-dev wx-common libogdi-dev unixodbc-dev \
    libwxbase3.2-0-unofficial libwxbase3.2unofficial-dev libwxgtk3.2-0-unofficial libwxgtk3.2unofficial-dev wx3.2-headers \
    build-essential cmake unzip wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install SAGA GIS 9.3.1
RUN wget -O saga-9.3.1_src.zip "https://sourceforge.net/projects/saga-gis/files/SAGA%20-%209/SAGA%20-%209.3.1/saga-9.3.1_src.zip/download" \
    && unzip saga-9.3.1_src.zip -d saga_src \
    && mkdir saga_src/saga-9.3.1/saga-gis/build \
    && cd saga_src/saga-9.3.1/saga-gis/build \
    && cmake .. \
    && make -j$(nproc) \
    && make install \
    && cd /app \
    && rm -rf saga_src saga-9.3.1_src.zip

# Copy the current directory contents into the container at /app
# COPY . /app

# Install any necessary Python dependencies from requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Set environment variables, including LD_LIBRARY_PATH
ENV QGIS_PREFIX_PATH=/usr \
    QT_QPA_PLATFORM=offscreen \
    XDG_RUNTIME_DIR=/tmp/runtime-root \
    LD_LIBRARY_PATH=/usr/lib/grass78/lib:/usr/local/lib:${LD_LIBRARY_PATH}

# Keep the container running
CMD ["tail", "-f", "/dev/null"]

