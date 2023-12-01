# coding: utf-8
# Oppdatert 25. september 2020

import arcpy, os, shutil, time, sys, urllib2, zipfile
print("Python-modulene er lastet inn - nå starter showet " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()


# Setter parametre -------------------------------------------------------

# Alle geodatafiler må vare i koordinatsystem 25833 (Euref89, sone 33)

# Ni resultatdatasett:
# - dreneringslinjer_ferdig_aapen
# - dreneringslinjer_ferdig_tett
# - dreneringslinjer_ferdig_web_aapen (glattet)
# - dreneringslinjer_ferdig_web_tett (glattet)
# - forsenkninger_ferdig_aapen
# - forsenkninger_ferdig_tett
# - stikkrenner_linje
# - stikkrenner_flate
# - flate_omraader


omraadevalg_P_polygonfil = "E:\Vannveger\\Grunnlagsdata\\polygonfil.gdb\\Polygon_Aukra"

arbeidskatalog = "E:\Vannveger"
#fkb_bygning_fil = "E:\Vannveger\\Grunnlagsdata\\FKB\\GDB_FKB_Bygning.gdb\\Bygg_flate"
#fkb_vann_flate_fil = "E:\Vannveger\\Grunnlagsdata\\FKB\\GDB_FKB_Vann.gdb\\Vann_flate"
#fkb_vann_linje_fil = "E:\Vannveger\\Grunnlagsdata\\FKB\\GDB_FKB_Vann.gdb\\Vann_linje"
#fkb_bygningsmessige_anlegg_linje_fil = "E:\Vannveger\Grunnlagsdata\FKB\GDB_FKB_BygnAnlegg.gdb\BygnAnlegg_linje"
fkb_bygning_fil = "E:\Vannveger\\Grunnlagsdata\\FKB\\Basisdata_0000_Norge_5973_FKB-Bygning_FGDB.gdb\\fkb_bygning_omrade"
fkb_vann_flate_fil = "E:\Vannveger\\Grunnlagsdata\\FKB\\Basisdata_0000_Norge_5973_FKB-Vann_FGDB.gdb\\fkb_vann_omrade"
fkb_vann_linje_fil = "E:\Vannveger\\Grunnlagsdata\\FKB\\Basisdata_0000_Norge_5973_FKB-Vann_FGDB.gdb\\fkb_vann_grense"
fkb_bygningsmessige_anlegg_linje_fil = "E:\Vannveger\Grunnlagsdata\FKB\Basisdata_0000_Norge_5973_FKB-BygnAnlegg_FGDB.gdb\\fkb_bygnanlegg_senterlinje"
nvdb_stikkrenner_linje = "E:\Vannveger\\Grunnlagsdata\\StikkrenneKulvert_79.gdb\\StikkrenneKulvert_79_LINJE"
#nvdb_stikkrenner_linje = "E:\Vannveger\\Grunnlagsdata\\nvdb.gdb\\StikkrenneKulvert_79_LINJE"
#nvdb_stikkrenner_linje = "E:\Vannveger\\Grunnlagsdata\\StikkrenneKulvert_79_34.gdb\\StikkrenneKulvert_79_34_LINJE"
#nvdb_stikkrenner_linje = "E:\Vannveger\\Grunnlagsdata\\StikkrenneKulvert_79_50.gdb\\StikkrenneKulvert_79_50_LINJE"
kommunalt_stikkrennedatasett_linje = "E:\\Vannveger\\Grunnlagsdata\\Sikkrenner_komm.gdb\\stikkrenner_kommune_linje"
kommunalt_stikkrennedatasett_flate = "E:\\Vannveger\\Grunnlagsdata\\Sikkrenner_komm.gdb\\stikkrenner_kommune_flate"
#reginefil = "E:\\Vannveger\\Grunnlagsdata\\NVE_data\\NVEData.gdb\\Nedborfelt\\RegineEnhet"
reginefil = "E:\\Vannveger\\Grunnlagsdata\\NVE_data\\NVEData.gdb\\Nedborfelt\\RegineEnhetClip"
#dtm10wcs = "https://wms.geonorge.no/skwms1/wcs.hoyde-dtm10_33?"
dtm10wcs = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?"
dtm1_filer = arbeidskatalog + "\\\\Grunnlagsdata\\Hoydedata\\Hoydegrid_NDH_Aukra\\dtm1\\data"
#nhm_metadata_url = "https://hoydedata.no/LaserInnsyn/Home/DownloadFile/57"
nhm_metadata_url = "https://hoydedata.no/LaserServices/REST/DownloadFile.ashx?id=57"
kommuner = "E:\\Arbeid\\Dreneringslinjer\\fylkesbase\\Basisdata_0000_Norge_25833_Kommuner_FGDB.gdb\\kommune"
# Den neste verdien kan være 1 eller 0.25. Hvis den er 0.25, så brukes 25cm dtm.
cellestr = 1


# -------------------------------------------------------------------------


koordsys = "PROJCS['ETRS_1989_UTM_Zone_33N',GEOGCS['GCS_ETRS_1989',DATUM['D_ETRS_1989',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',15.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")


# Starter jobben ----------------------------------------------------------


# Oppretter omraadekatalog
arcpy.MakeFeatureLayer_management(omraadevalg_P_polygonfil, "omraade_layer")
omraadekatalog = "p_" + omraadevalg_P_polygonfil.rsplit("\\",1)[1]
if ".shp" in omraadekatalog:
    omraadekatalog = omraadekatalog[:-4]
arbeidskatalog = arbeidskatalog + "\\" + omraadekatalog
arbeidsgeodatabase = omraadekatalog
os.mkdir(arbeidskatalog)


# Oppretter logfil
logfil = open(arbeidskatalog + "\\" + omraadekatalog + "_logfil.txt","w")
logfil.write("Produksjon av dreneringslinjer for område: " + omraadekatalog + "\n")
logfil.write("Startet kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
logfil.write("--------------------------------------------------------- \n")


# Lager filgeodatabase
print("Lager filgeodatabase " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Lager filgeodatabase kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
arcpy.CreateFileGDB_management(arbeidskatalog, arbeidsgeodatabase)
os.mkdir(arbeidskatalog + "\\" + arbeidsgeodatabase + "_temp_reclassfiler")


# Velger riktige Regine-enheter
print("Velger regine-enheter basert på område " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Velger regine-enheter basert på område kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
arcpy.MakeFeatureLayer_management(reginefil, "regine_layer")
arcpy.SelectLayerByLocation_management("regine_layer", "INTERSECT", "omraade_layer", "", "NEW_SELECTION")
arcpy.CopyFeatures_management("regine_layer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt")
arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt", "regine_dissolve", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt", "regine_dissolve", "97", "PYTHON_9.3", "")
arcpy.Dissolve_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_dissolve", "regine_dissolve")
# Finner store havflater som skal klippes vekk fra Regine-enhetene
arcpy.MakeFeatureLayer_management(fkb_vann_flate_fil, "hav_flate_klipp_layer", "(objtype = 'Havflate' OR  OBJTYPE = 'Havflate')")
arcpy.Erase_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_dissolve", "hav_flate_klipp_layer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_dissolve_erase",'#')
arcpy.Buffer_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_dissolve_erase", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer", "500 Meters")


# Lager en mosaikk av alle flisene av DTM1/DTM025
print("Lager mosaikk med alle høydedataflisene " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Lager mosaikk med alle høydedataflisene kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
arcpy.CreateMosaicDataset_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb", "mosaic_dtm1", koordsys)
arcpy.AddRastersToMosaicDataset_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\mosaic_dtm1", "Raster Dataset", dtm1_filer)


# Klipper DTM1
print("Klipper DTM1-fliser kl. " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Klipper DTM1-fliser kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
feature8 = arcpy.Describe(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer")
extent8 = feature8.extent
rect = "{0} {1} {2} {3}".format(extent8.XMin, extent8.YMin, extent8.XMax, extent8.YMax)
arcpy.env.compression = "PackBits"
arcpy.env.pyramid = "NONE"
arcpy.Clip_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\mosaic_dtm1", rect, arbeidskatalog + "\\dtm1_ruter.tif", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer", "#", "ClippingGeometry", "NO_MAINTAIN_EXTENT")


# Sjekker at område er 100% dekket av 1m/25cm grid - hvis ikke så fylles området med 10m grid
print("Sjekker at området er 100% dekket av 1m/25cm høydegrid " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Sjekker at området er 100% dekket av 1m/25cm høydegrid kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
remapTable2 = arcpy.sa.RemapRange([ ["NODATA", 1], [0.0000000000001, 99999999, 2] ])
arcpy.env.workspace = arbeidskatalog + "\\" + arbeidsgeodatabase + "_temp_reclassfiler"
reclassRaster2 = arcpy.sa.Reclassify(arbeidskatalog + "\\dtm1_ruter.tif", "Value", remapTable2, "NODATA")
reclassRaster2.save(arbeidskatalog + "\\dtm1_reclass.tif")
arcpy.RasterToPolygon_conversion(arbeidskatalog + "\\dtm1_reclass.tif", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm1_mangler")
arcpy.Clip_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm1_mangler", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm1_mangler2")
arcpy.MakeTableView_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm1_mangler2", "myTableView2")
utenfor2 = int(arcpy.GetCount_management("myTableView2").getOutput(0))
if utenfor2 > 0:
    print("-- Ikke fullstendig dekning av DTM1/DTM025 - henter DTM10 fra WCS-tjeneste " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- Ikke fullstendig dekning av DTM1/DTM025 - henter DTM10 fra WCS-tjeneste kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.MakeFeatureLayer_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm1_mangler2", "dtm1_mangler2_layer", "gridcode = 1")
    arcpy.Buffer_analysis("dtm1_mangler2_layer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm1_mangler_10m_buffer", "20 Meters")
    arcpy.MakeWCSLayer_management(dtm10wcs, "wcs_layer_dtm10")
    feature2 = arcpy.Describe(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm1_mangler_10m_buffer")
    extent2 = feature2.extent
    rect2 = "{0} {1} {2} {3}".format(extent2.XMin, extent2.YMin, extent2.XMax, extent2.YMax)
    arcpy.env.compression = "PackBits"
    arcpy.env.pyramid = "NONE"
    arcpy.Clip_management("wcs_layer_dtm10", rect2, arbeidskatalog + "\\dtm10_fra_wcs.tif", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm1_mangler_10m_buffer", "#", "ClippingGeometry", "NO_MAINTAIN_EXTENT")
    print("-- Lager heldekkende raster av DTM1 og DTM10 " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    arcpy.env.workspace = arbeidskatalog
    arcpy.MosaicToNewRaster_management("dtm1_ruter.tif;dtm10_fra_wcs.tif", arbeidskatalog, "dtm1_for_hele_omraadet.tif", koordsys, "32_BIT_FLOAT", "1", "1", "FIRST","FIRST")
else:
    print("--  Området er 100% dekket av 1m/0.25m høydegrid " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("--  Området er 100% dekket av 1m/0.25m høydegrid kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.CopyRaster_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\mosaic_dtm1", arbeidskatalog + "\\dtm1_for_hele_omraadet.tif")


# Stikkrennehåndtering starter --------------------------------------------

# Finner stikkrenner som skal svis ned i terrengmodellen
arcpy.CopyRaster_management(arbeidskatalog + "\\dtm1_for_hele_omraadet.tif", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terrengmodell_stikkrenner_tett")
print("Finner stikkrenner som skal svis ned i terrengmodellen " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Finner stikkrenner som skal svis ned i terrengmodellen kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")


arcpy.MakeFeatureLayer_management(fkb_bygningsmessige_anlegg_linje_fil, "stikkrenner_stikkrenner_kulverter_fkb_bygnanl_layer", "objtype = 'Kulvert' OR  OBJTYPE = 'Kulvert' OR objtype = 'Stikkrenne' OR  OBJTYPE = 'Stikkrenne'")
arcpy.MakeFeatureLayer_management(nvdb_stikkrenner_linje, "stikkrenner_nvdb_layer")
arcpy.MakeFeatureLayer_management(fkb_vann_linje_fil, "stikkrenner_fkb_vann_medium_u_linje_layer", "(MEDIUM = 'U' OR medium = 'U') AND (OBJTYPE = 'ElvBekk' OR OBJTYPE = 'KanalGrøft' OR objtype = 'ElvBekk' OR objtype = 'KanalGrøft')")
arcpy.MakeFeatureLayer_management(fkb_vann_flate_fil, "stikkrenner_fkb_vann_medium_u_flate_layer", "MEDIUM = 'U' OR medium = 'U'")
stikkrenneliste = ["stikkrenner_kulverter_fkb_bygnanl", "nvdb", "fkb_vann_medium_u_linje", "fkb_vann_medium_u_flate"]
if arcpy.Exists(kommunalt_stikkrennedatasett_linje):
    arcpy.MakeFeatureLayer_management(kommunalt_stikkrennedatasett_linje, "stikkrenner_kommunale_ekstradata_linje_layer")
    stikkrenneliste.append("kommunale_ekstradata_linje")

if arcpy.Exists(kommunalt_stikkrennedatasett_flate):
    arcpy.MakeFeatureLayer_management(kommunalt_stikkrennedatasett_flate, "stikkrenner_kommunale_ekstradata_flate_layer")
    stikkrenneliste.append("kommunale_ekstradata_flate")

for stikkrennetype in stikkrenneliste:
    arcpy.SelectLayerByLocation_management("stikkrenner_" + stikkrennetype + "_layer", "intersect", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer", "", "NEW_SELECTION")
    antallobjekter = int(arcpy.GetCount_management("stikkrenner_" + stikkrennetype + "_layer").getOutput(0))
    print("-- Stikkrennetype: " + stikkrennetype + ": " + str(antallobjekter) + " i området.")
    sys.stdout.flush()
    logfil.write("-- Stikkrennetype: " + stikkrennetype + ": " + str(antallobjekter) + " i området." + "\n")
    if antallobjekter > 0:
        arcpy.env.outputZFlag = "Disabled"
        arcpy.CopyFeatures_management("stikkrenner_" + stikkrennetype + "_layer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype)
        arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype, "KILDE", "TEXT", "", "", 40, "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype, "KILDE", '"' + stikkrennetype + '"', "PYTHON_9.3", "")

stikkrennetype_alle = []
stikkrennetype_linje_ut = []
stikkrennetype_flate_ut = []

for stikkrennetype_linje in ["stikkrenner_kulverter_fkb_bygnanl", "nvdb", "fkb_vann_medium_u_linje", "kommunale_ekstradata_linje"]:
    if arcpy.Exists(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_linje):
        fieldObjList = arcpy.ListFields(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_linje)
        fieldNameList = []
        for field in fieldObjList:
            if not field.required and not field.name == "KILDE":
                    fieldNameList.append(field.name)
        if len(fieldNameList) > 0:
            arcpy.DeleteField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_linje, fieldNameList)
        arcpy.Buffer_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_linje, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_linje + "_buffer", cellestr, "", "FLAT")
        stikkrennetype_alle.append(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_linje + "_buffer")
        stikkrennetype_linje_ut.append(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_linje)

if len(stikkrennetype_linje_ut) > 0:
    if len(stikkrennetype_linje_ut) < 2:
        for stikkrennetype_linje_ut_single in stikkrennetype_linje_ut:
            arcpy.CopyFeatures_management(stikkrennetype_linje_ut_single, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_linje")
    else:
        arcpy.Merge_management(stikkrennetype_linje_ut, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_linje")
    print("-- Stikkrenner med linjetopologi blir kopiert ut til fila 'stikkrenner_linje'.")
    sys.stdout.flush()
    logfil.write("-- Stikkrenner med linjetopologi blir kopiert ut til fila 'stikkrenner_linje'." + "\n")

for stikkrennetype_flate in ["fkb_vann_medium_u_flate", "kommunale_ekstradata_flate"]:
    if arcpy.Exists(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_flate):
        fieldObjList = arcpy.ListFields(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_flate)
        fieldNameList = []
        for field in fieldObjList:
            if not field.required and not field.name == "KILDE":
                    fieldNameList.append(field.name)
        if len(fieldNameList) > 0:
            arcpy.DeleteField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_flate, fieldNameList)
        stikkrennetype_alle.append(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_flate)
        stikkrennetype_flate_ut.append(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_" + stikkrennetype_flate)

if len(stikkrennetype_flate_ut) > 0:
    if len(stikkrennetype_flate_ut) < 2:
        for stikkrennetype_flate_ut_single in stikkrennetype_flate_ut:
            arcpy.CopyFeatures_management(stikkrennetype_flate_ut_single, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_flate")
    else:
        arcpy.Merge_management(stikkrennetype_flate_ut, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\stikkrenner_flate")
    print("-- Stikkrenner med flatetopologi blir kopiert ut til fila 'stikkrenner_flate'.")
    sys.stdout.flush()
    logfil.write("-- Stikkrenner med flatetopologi blir kopiert ut til fila 'stikkrenner_flate'." + "\n")


if len(stikkrennetype_alle) > 0:
    for stikkrenner_alle in stikkrennetype_alle:
        fieldObjList = arcpy.ListFields(stikkrenner_alle)
        fieldNameList = []
        for field in fieldObjList:
            if not field.required and not field.name == "KILDE":
                    fieldNameList.append(field.name)
        if len(fieldNameList) > 0:
            arcpy.DeleteField_management(stikkrenner_alle, fieldNameList)
    if len(stikkrennetype_alle) < 2:
        for stikkrenner_alle in stikkrennetype_alle:
            arcpy.CopyFeatures_management(stikkrenner_alle, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_under_bakken")
    else:
        arcpy.Merge_management(stikkrennetype_alle, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_under_bakken")

arcpy.MakeTableView_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_under_bakken", "myTableView_vannkanaler")
antall_vannkanaler = int(arcpy.GetCount_management("myTableView_vannkanaler").getOutput(0))
if antall_vannkanaler > 0:
    print("-- I alt er det " + str(antall_vannkanaler) + " stikkrenner og lignende i området.")
    sys.stdout.flush()
    logfil.write("-- I alt er det " + str(antall_vannkanaler) + " stikkrenner og lignende i området." + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_under_bakken", "z_hoyde", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_under_bakken", "z_hoyde", "-10", "PYTHON_9.3", "")
    feature3 = arcpy.Describe(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer")
    arcpy.env.extent = feature3.extent
    arcpy.FeatureToRaster_conversion(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_under_bakken", "z_hoyde", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_raster", cellestr)
    arcpy.gp.IsNull_sa(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_raster", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_raster_isnull")
    arcpy.gp.Con_sa(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_raster_isnull", "0", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_raster_rett", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_raster", "Value = 1")
    arcpy.gp.Plus_sa(arbeidskatalog + "\\dtm1_for_hele_omraadet.tif", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_raster_rett", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terrengmodell_stikkrenner_aapen")
else:
    print("-- Det finnes ingen objekter")
    sys.stdout.flush()
    logfil.write("-- Det finnes ingen objekter kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.CopyRaster_management(arbeidskatalog + "\\dtm1_for_hele_omraadet.tif", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terrengmodell_stikkrenner_aapen")

# Stikkrennehåndtering avsluttes --------------------------------------------


# Velger bygninger som skal vare med i terrengmodellen
print("Finner bygninger som skal være med i terrengmodellen " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Finner bygninger som skal være med i terrengmodellen kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
arcpy.MakeFeatureLayer_management(fkb_bygning_fil, "bygning_layer", "OBJTYPE = 'Bygning' OR OBJTYPE = 'AnnenBygning'")
arcpy.SelectLayerByLocation_management("bygning_layer", "intersect", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer", "", "NEW_SELECTION")
arcpy.CopyFeatures_management("bygning_layer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygning_tett")
arcpy.SelectLayerByLocation_management("bygning_layer", "intersect", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_under_bakken", "", "REMOVE_FROM_SELECTION")
arcpy.CopyFeatures_management("bygning_layer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygning_aapen")


# Finner store vannflater som definerer hvilke områder som skal klippes vekk fra resultater
print("Finner store vannflater som definerer hvilke områder som skal klippes vekk fra resultater " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Finner store vannflater som definerer hvilke områder som skal klippes vekk fra resultater kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
arcpy.MakeFeatureLayer_management(fkb_vann_flate_fil, "vann_flate_klipp_layer", "(objtype = 'Innsjø' OR  OBJTYPE = 'Innsjø') AND (SHAPE_Area > 100000 OR Shape_Area > 100000)")
arcpy.SelectLayerByLocation_management("vann_flate_klipp_layer", "intersect", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer", "", "NEW_SELECTION")
arcpy.CopyFeatures_management("vann_flate_klipp_layer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vann_flate_klipp")


liste = ("tett", "aapen")
for stikkrenner in liste:

    logfil.write("Videre prosessering - med stikkrenner " + stikkrenner + "\n")
    logfil.write("------------------------------------------------------- \n")
    print("Videre prosessering - med stikkrenner " + stikkrenner +": " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()

    # Lager bygningsraster
    print("-- " + stikkrenner + ": Lager bygningsraster " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Lager bygningsraster kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.MakeTableView_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygning_" + stikkrenner, "myTableView_bygg_" + stikkrenner)
    antall_bygg = int(arcpy.GetCount_management("myTableView_bygg_" + stikkrenner).getOutput(0))
    if antall_bygg > 0:
        arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygning_" + stikkrenner, "z_hoyde", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygning_" + stikkrenner, "z_hoyde", "10", "PYTHON_9.3", "")
        arcpy.FeatureToRaster_conversion(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygning_" + stikkrenner, "z_hoyde", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygninger_raster_" + stikkrenner, cellestr)
        feature = arcpy.Describe(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt_buffer")
        arcpy.env.extent = feature.extent
        outIsNull = arcpy.sa.IsNull(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygninger_raster_" + stikkrenner)
        outIsNull.save(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygninger_raster_isnull_" + stikkrenner)
        arcpy.gp.Con_sa(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygninger_raster_isnull_" + stikkrenner, "0", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygninger_raster_rett_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygninger_raster_" + stikkrenner, "Value = 1")
        print("-- " + stikkrenner + ": Legger sammen terrengmodell og bygningsraster " + time.strftime("%H:%M:%S", time.localtime()))
        sys.stdout.flush()
        logfil.write("-- " + stikkrenner + ": Legger sammen terrengmodell og bygningsraster kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
        arcpy.gp.Plus_sa(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terrengmodell_stikkrenner_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\bygninger_raster_rett_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terreng_med_bygninger_raster_" + stikkrenner)
    else:
        arcpy.Rename_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terrengmodell_stikkrenner_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terreng_med_bygninger_raster_" + stikkrenner)


    # Fyller forsenkninger i terrengmodellen
    print("-- " + stikkrenner + ": Fyller forsenkninger i terrengmodellen " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Fyller forsenkninger i terrengmodellen " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.gp.Fill_sa(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terreng_med_bygninger_raster_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terreng_stikkrenner_fill_" + stikkrenner, "")
    if stikkrenner == "tett":
        # Finner flate områder
        # - gjør dette i loopen med tett/aapen, så en unngår å kjøre fill flere ganger enn nødvendig
        print("-- Finner flate områder, som seinere skal definere områder som skal klippes bort")
        sys.stdout.flush()
        logfil.write("Finner flate områder" + "\n")
        print("---- først resampling av terrengmodellen til lavere oppløsning " + time.strftime("%H:%M:%S", time.localtime()))
        sys.stdout.flush()
        logfil.write("---- først resampling av terrengmodellen til lavere oppløsning kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
        arcpy.Resample_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terreng_stikkrenner_fill_tett", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm_flat_for_hele_omraadet", "20", "BILINEAR")
        print("---- så slope av flat-dtm " + time.strftime("%H:%M:%S", time.localtime()))
        sys.stdout.flush()
        logfil.write("---- saa slope av flat-dtm kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
        arcpy.Slope_3d(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dtm_flat_for_hele_omraadet", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\slope_flat_for_hele_omraadet", "DEGREE", "1", "PLANAR", "METER")
        print("---- så reclassify av flat-slope " + time.strftime("%H:%M:%S", time.localtime()))
        sys.stdout.flush()
        logfil.write("---- så reclassify av flat-slope kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
        arcpy.Reclassify_3d(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\slope_flat_for_hele_omraadet", "VALUE", "0,00000000000001 0,500000 1;0,500000 99,9999999 NODATA", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\slope_flat_reclass_for_hele_omraadet", "DATA")
        arcpy.env.outputZFlag = "Disabled"
        print("---- så raster to polygon av flat-slope " + time.strftime("%H:%M:%S", time.localtime()))
        sys.stdout.flush()
        logfil.write("---- så raster to polygon av flat-slope kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
        arcpy.RasterToPolygon_conversion(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\slope_flat_reclass_for_hele_omraadet", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\slope_flat_poly_for_hele_omraadet", "NO_SIMPLIFY", "VALUE", "SINGLE_OUTER_PART", "")
        arcpy.MakeFeatureLayer_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\slope_flat_poly_for_hele_omraadet", "slope_poly_Layer", "Shape_Area >10000")
        antallobjekter = int(arcpy.GetCount_management("slope_poly_Layer").getOutput(0))
        if antallobjekter > 0:
            arcpy.CopyFeatures_management("slope_poly_Layer", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flate_omraader")
            arcpy.RemoveSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flate_omraader")
            arcpy.AddSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flate_omraader", 0,0,0)
            print("---- flate områder blir kopiert ut til fila 'flate_omraader'.")
            sys.stdout.flush()
            logfil.write("---- flate områder blir kopiert ut til fila 'flate_omraader'." + "\n")
        else:
            print("---- ingen flate områder ble funnet.")
            sys.stdout.flush()
            logfil.write("---- ingen flate områder ble funnet." + "\n")


    # Finner forsenkninger i terrengmodellen
    print("-- " + stikkrenner + ": Finner forsenkninger i terrengmodellen " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Finner forsenkninger i terrengmodellen kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.gp.Minus_sa(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terreng_stikkrenner_fill_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terreng_med_bygninger_raster_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_raster_" + stikkrenner)
    arcpy.CalculateStatistics_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_raster_" + stikkrenner)
    remapTable = arcpy.sa.RemapRange([ [-100, 0.5, "NODATA"], [0.5, 1, 1],[1, 2, 2],[2, 3, 3],[3, 999, 4] ])
    arcpy.env.workspace = arbeidskatalog + "\\" + arbeidsgeodatabase + "_temp_reclassfiler"
    reclassRaster = arcpy.sa.Reclassify(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_raster_" + stikkrenner, "Value", remapTable, "NODATA")
    arcpy.CopyRaster_management(reclassRaster, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_raster_reclass_" + stikkrenner)
    arcpy.RasterToPolygon_conversion(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_raster_reclass_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_raster_reclass_poly_" + stikkrenner)
    arcpy.MakeFeatureLayer_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_raster_reclass_poly_" + stikkrenner, "sink_layer_" + stikkrenner, "gridcode > 0 AND Shape_Area > 150")
    arcpy.CopyFeatures_management("sink_layer_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks_" + stikkrenner)
    arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks_" + stikkrenner, "dybde_fra_til_m", "TEXT", "", "", 20, "", "NULLABLE", "NON_REQUIRED", "")
    fields = ["gridcode", "dybde_fra_til_m"]
    with arcpy.da.UpdateCursor(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks_" + stikkrenner, fields) as cursor:
        for row in cursor:
            if row[0] == 1:
                row[1] = "05_1"
            elif row[0] == 2:
                row[1] = "1_2"
            elif row[0] == 3:
                row[1] = "2_3"
            elif row[0] == 4:
                row[1] = "3_eller_dypere"
            cursor.updateRow(row)
    arcpy.env.outputZFlag = "Disabled"
    arcpy.MakeFeatureLayer_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks_" + stikkrenner, "sink_layer2_" + stikkrenner, "SHAPE_Area > 100")
    arcpy.CopyFeatures_management("sink_layer2_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks2_" + stikkrenner)
    arcpy.DeleteField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks2_" + stikkrenner, ["Id","gridcode"])


    # Prosessering: flow direction
    print("-- " + stikkrenner + ": Prosessering: flow direction " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Prosessering: flow direction kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.gp.FlowDirection_sa(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\terreng_stikkrenner_fill_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowdirection_raster_" + stikkrenner, "NORMAL")


    # Prosessering: flow accumulation
    print("-- " + stikkrenner + ": Prosessering: flow accumulation " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Prosessering: flow accumulation kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.gp.FlowAccumulation_sa(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowdirection_raster_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowaccumulation_raster_" + stikkrenner, "", "FLOAT")


    # Prosessering: lager dreneringslinjer
    print("-- " + stikkrenner + ": Prosessering: lager dreneringslinjer " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Prosessering: lager dreneringslinjer kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.CalculateStatistics_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowaccumulation_raster_" + stikkrenner)
    rasterklasser = arcpy.sa.RemapRange([[0,10000/(cellestr*cellestr),"NODATA"],[10000/(cellestr*cellestr),20000/(cellestr*cellestr),1],[20000/(cellestr*cellestr),50000/(cellestr*cellestr),2],[50000/(cellestr*cellestr),100000/(cellestr*cellestr),3],[100000/(cellestr*cellestr),500000/(cellestr*cellestr),4],[500000/(cellestr*cellestr),1000000/(cellestr*cellestr),5],[1000000/(cellestr*cellestr),9999999999,6]])
    arcpy.env.workspace = arbeidskatalog + "\\" + arbeidsgeodatabase + "_temp_reclassfiler"
    outReclass2 = arcpy.sa.Reclassify(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowaccumulation_raster_" + stikkrenner, "Value", rasterklasser)
    arcpy.CopyRaster_management(outReclass2, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowaccumulation_raster_reclass_" + stikkrenner)
    #arcpy.RasterToPolyline_conversion(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowaccumulation_raster_reclass_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_" + stikkrenner, "ZERO", "0", "SIMPLIFY", "VALUE")
    arcpy.sa.StreamToFeature(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowaccumulation_raster_reclass_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\flowdirection_raster_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_" + stikkrenner, "SIMPLIFY")
    arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_" + stikkrenner, "areal_fra_til_m2", "TEXT", "", "", 20, "", "NULLABLE", "NON_REQUIRED", "")
    fields = ["grid_code", "areal_fra_til_m2"]
    with arcpy.da.UpdateCursor(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_" + stikkrenner, fields) as cursor:
        for row in cursor:
            if row[0] == 1:
                row[1] = "10000_20000"
            elif row[0] == 2:
                row[1] = "20000_50000"
            elif row[0] == 3:
                row[1] = "50000_100000"
            elif row[0] == 4:
                row[1] = "100000_500000"
            elif row[0] == 5:
                row[1] = "500000_1000000"
            elif row[0] == 6:
                row[1] = "1000000_eller_mer"
            cursor.updateRow(row)


    # Fjerner z-feltet fra dataene
    arcpy.env.outputZFlag = "Disabled"


    # Klipper vekk data der det er store vannflater
    print("-- " + stikkrenner + ": Klipper vekk data der det er store vannflater " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Klipper vekk data der det er store vannflater kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    antallobjekter = int(arcpy.GetCount_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vann_flate_klipp").getOutput(0))
    if antallobjekter > 0:
        arcpy.Erase_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vann_flate_klipp", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_2_" + stikkrenner, "")
        arcpy.Erase_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks2_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vann_flate_klipp", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks3_" + stikkrenner, "")
    else:
        arcpy.Rename_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_2_" + stikkrenner)
        arcpy.Rename_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks2_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks3_" + stikkrenner)
    arcpy.Clip_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_2_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_3_" + stikkrenner)
    arcpy.Clip_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\sinks3_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_ferdig_" + stikkrenner)


    # Legger til attributt som forteller om vannveien er over eller under bakken
    print("-- " + stikkrenner + ": Legger til attributt som forteller om vannveien er over eller under bakken " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Legger til attributt som forteller om vannveien er over eller under bakken kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_3_" + stikkrenner, "MEDIUM", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    if stikkrenner == "aapen" and antall_vannkanaler > 0:
        arcpy.Identity_analysis (arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_3_aapen", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\vannkanaler_under_bakken", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_medium_aapen", "NO_FID")
        fields = ["KILDE", "MEDIUM"]
        with arcpy.da.UpdateCursor(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_medium_aapen", fields) as cursor:
            for row in cursor:
                if row[0] <> "":
                    row[1] = "U"
                elif row[0] == "":
                    row[1] = "T"
                cursor.updateRow(row)
    else:
        arcpy.Rename_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_3_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_medium_" + stikkrenner)
        arcpy.CalculateField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_medium_" + stikkrenner, "MEDIUM", "\"T\"", "PYTHON", "")



    # Knytter sammen linjer med like egenskaper
    print("-- " + stikkrenner + ": Knytter sammen linjer med like egenskaper " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Knytter sammen linjer med like egenskaper kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.Dissolve_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_medium_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_" + stikkrenner, "areal_fra_til_m2;MEDIUM", "", "SINGLE_PART", "UNSPLIT_LINES")


    # Glatting av dataene som brukes i webkartlosninger
    print("-- " + stikkrenner + ": Glatting av dataene som brukes i webkartlosninger " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Glatting av dataene som brukes i webkartlosninger kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.SimplifyLine_cartography(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_" + stikkrenner, arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_web_" + stikkrenner, "BEND_SIMPLIFY", "10 Meters", "RESOLVE_ERRORS", "NO_KEEP", "CHECK", "")


    # Sletting av unødvendige felt
    print("-- " + stikkrenner + ": Sletting av unødvendige felt " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Sletting av unødvendige felt kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    dropFields = ["InLine_FID", "SimLnFlag", "MaxSimpTol", "MinSimpTol","grid_code", "arcid", "from_node", "to_node", "FID_vannkanaler_under_bakken", "FID_dreneringslinjer_3_aapen"]
    arcpy.DeleteField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_web_" + stikkrenner, dropFields)
    arcpy.DeleteField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_" + stikkrenner, dropFields)


    # Lager nye romlige indexer på nytt
    print("-- " + stikkrenner + ": Lager nye romlige indexer på nytt " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- " + stikkrenner + ": Lager nye romlige indexer på nytt kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
    arcpy.RemoveSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_" + stikkrenner)
    arcpy.RemoveSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_web_" + stikkrenner)
    arcpy.RemoveSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_ferdig_" + stikkrenner)
    arcpy.AddSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_" + stikkrenner, 0,0,0)
    arcpy.AddSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dreneringslinjer_ferdig_web_" + stikkrenner, 0,0,0)
    arcpy.AddSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\forsenkninger_ferdig_" + stikkrenner, 0,0,0)


#Lager dekningskart
print("Lager dekningskart " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Lager dekningskart kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")
try:
    nhm_metadata = urllib2.urlopen(nhm_metadata_url)
    with open(arbeidskatalog + "\\nhm_metadata.zip",'wb') as output:
        output.write(nhm_metadata.read())
    os.mkdir(arbeidskatalog + "\\nhm_metadata")
    with zipfile.ZipFile(arbeidskatalog + "\\nhm_metadata.zip", 'r') as zip_ref:
        zip_ref.extractall(arbeidskatalog + "\\nhm_metadata")
    arcpy.Clip_analysis(arbeidskatalog + "\\nhm_metadata\\NHM_ProsjektDekning.shp", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dekningskart")
    arcpy.Erase_analysis(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\regine_utvalgt", arbeidskatalog + "\\nhm_metadata\\NHM_ProsjektDekning.shp", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\prosessert_omr_uten_nhm_dekningskart", "")
    arcpy.MakeTableView_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\prosessert_omr_uten_nhm_dekningskart", "myTableView25")
    utenfor25 = int(arcpy.GetCount_management("myTableView25").getOutput(0))
    if utenfor25 > 0:
        desc = arcpy.Describe(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\prosessert_omr_uten_nhm_dekningskart")
        fieldObjList = arcpy.ListFields(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\prosessert_omr_uten_nhm_dekningskart")
        fieldNameList = []
        for field in fieldObjList:
            if not field.required:
                fieldNameList.append(field.name)
        arcpy.DeleteField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\prosessert_omr_uten_nhm_dekningskart", fieldNameList)
        arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\prosessert_omr_uten_nhm_dekningskart", "PROSJNAVN", "TEXT", "", "", 30, "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\prosessert_omr_uten_nhm_dekningskart", "PROSJNAVN", "\"Data fra DTM10\"", "PYTHON_9.3", "")
        arcpy.Append_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\prosessert_omr_uten_nhm_dekningskart", arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dekningskart", "NO_TEST")
        arcpy.AddField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dekningskart", "PRODUKSJONSDATO", "DATE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dekningskart", "PRODUKSJONSDATO", "time.strftime('%d/%m/%Y')", "PYTHON_9.3", "")
        arcpy.RemoveSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dekningskart")
        arcpy.AddSpatialIndex_management(arbeidskatalog + "\\" + arbeidsgeodatabase + ".gdb\\dekningskart", 0,0,0)
except:
    print("-- Produksjon av dekningskart feilet " + time.strftime("%H:%M:%S", time.localtime()))
    sys.stdout.flush()
    logfil.write("-- Produksjon av dekningskart feilet kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n")


# Skriptet er ferdig
print("Ferdig!! " + time.strftime("%H:%M:%S", time.localtime()))
sys.stdout.flush()
logfil.write("Prosessering er ferdig kl. " + time.strftime("%H:%M:%S", time.localtime()) + "\n \n")
logfil.write("--------------------------------------------------------- \n \n \n")
logfil.close()
