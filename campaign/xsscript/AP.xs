int itemArray = -1;
int locationArray = -1;

void Init()
{
    itemArray = xsArrayCreateInt(12, -1, "Item Array");
    locationArray = xsArrayCreateInt(0, -1, "Location Array");
}

void AP_Write()
{
    xsCreateFile(false);
    xsWriteInt(1);
    xsWriteInt(xsGetGameTime());
    xsWriteFloat(6.5);
    xsWriteInt(2); 
    xsWriteInt(0);
    for (i = 0; < 12) {
        xsWriteInt(xsArrayGetInt(itemArray, i));
    }
    for (i = 0; < 31) {
    xsWriteInt(i);
    }
    for (i = 0; < xsArrayGetSize(locationArray)) {
        xsWriteInt(xsArrayGetInt(locationArray, i));
    }
    xsCloseFile();
}

void AP_Check_Location(int locationId)
{
    xsArrayResizeInt(locationArray, xsArrayGetSize(locationArray) + 1);
    xsArraySetInt(locationArray, xsArrayGetSize(locationArray), locationId);
}