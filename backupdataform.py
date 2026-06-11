const tablasSAP = [
    
    { nombre: "Z_BUT000",pks: ["CLIENT", "PARTNER"], campoFecha: "GLCHANGETIME",campoBorrado: "GLDELFLAG",},
    { nombre: "Z_EVER",pks: ["VERTRAG"],campoFecha: "GLCHANGETIME",campoBorrado: "GLDELFLAG",},
    { nombre: "Z_EIDESWTMSGDATA", pks: ["SWITCHNUM", "MSGDATANUM"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_VBAP", pks: ["VBELN", "POSNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ANEP", pks: ["BUKRS", "ANLN1", "ANLN2", "GJAHR", "LNRAN", "AFABE", "ZUJHR", "ZUCOD"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ANEK", pks: ["BUKRS", "ANLN1", "ANLN2", "GJAHR", "LNRAN"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ANLP", pks: ["BUKRS", "GJAHR", "PERAF", "AFBNR", "ANLN1", "ANLN2", "AFABER", "ZUJHR", "ZUCOD"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_BUT020", pks: ["CLIENT", "PARTNER", "ADDRNUMBER"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_SWW_WI2OBJ", pks: ["CLIENT","GUID"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG",campoClustering: ["GLREQUEST"] },




   /* 
    { nombre: "Z_SWW_WI2OBJ", pks: ["CLIENT","GUID"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ADR6", pks: ["CLIENT", "ADDRNUMBER", "PERSNUMBER", "DATE_FROM", "CONSNUMBER"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ADRC", pks: ["CLIENT", "ADDRNUMBER", "DATE_FROM", "NATION"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ADRSTREET", pks: ["CLIENT", "COUNTRY", "STRT_CODE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_AFIH", pks: ["AUFNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_AFKO", pks: ["AUFNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ANKT", pks: ["SPRAS", "ANLKL"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ANLA", pks: ["BUKRS", "ANLN1", "ANLN2"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ANLB", pks: ["BUKRS", "ANLN1", "ANLN2", "AFABE", "BDATU"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_AUFK", pks: ["AUFNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_AUSP", pks: ["OBJEK", "ATINN", "ATZHL", "MAFID", "KLART", "ADZHL"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_BKPF", pks: ["BUKRS", "BELNR", "GJAHR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_BSEG", pks: ["BUKRS", "BELNR", "GJAHR", "BUZEI"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_CDHDR", pks: ["OBJECTCLAS", "OBJECTID", "CHANGENR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_CDPOS", pks: ["OBJECTCLAS", "OBJECTID", "CHANGENR", "TABNAME", "TABKEY", "FNAME", "CHNGIND"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_COBK", pks: ["KOKRS", "BELNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DBERCHZ1", pks: ["BELNR", "BELZEILE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DBERCHZ2", pks: ["BELNR", "BELZEILE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DBERCHZ3", pks: ["BELNR", "BELZEILE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DBERDL", pks: ["PRINTDOC", "PRINTDOCLINE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DBERDLB", pks: ["PRINTDOC", "PRINTDOCLINE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DFKKBPTAXNUM", pks: ["PARTNER", "TAXTYPE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DFKKKO", pks: ["OPBEL"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DFKKOP", pks: ["OPBEL", "OPUPW", "OPUPK", "OPUPZ"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_DFKKOPK", pks: ["OPBEL", "OPUPK"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EABL", pks: ["ABLBELNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EABLG", pks: ["ABLBELNR", "ANLAGE", "ABLESGR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EANL", pks: ["ANLAGE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EANLH", pks: ["ANLAGE", "BIS"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EHAUISU", pks: ["HAUS"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EIDESWTDOC", pks: ["SWITCHNUM"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },

    { nombre: "Z_EGERH", pks: ["EQUNR", "BIS"], campoFecha: "GLREQUEST DESC, BIS"}

    { nombre: "Z_EKKN", pks: ["EBELN", "EBELP", "ZEKKN"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EKKO", pks: ["EBELN"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EKPO", pks: ["EBELN", "EBELP"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EPREIH", pks: ["TWAERS", "PREIS", "PREISTYP", "PREISTUF", "BISDATUM", "VONZONE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EPROFHEAD", pks: ["PROFILE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EPROFHEADT", pks: ["PROFILE", "SPRAS"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EPROFVAL60", pks: ["PROFILE", "VALUEDAY"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EQKT", pks: ["EQUNR", "SPRAS"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EQUI", pks: ["EQUNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EQUZ", pks: ["EQUNR", "DATBI", "EQLFN"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ERCH", pks: ["BELNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ERDB", pks: ["OPBEL", "LFDNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ERDK", pks: ["OPBEL"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ETTIFN", pks: ["ANLAGE", "OPERAND", "SAISON", "AB", "ABLFDNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EUIINSTLN", pks: ["INT_UI", "ANLAGE", "DATETO", "TIMETO"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EUITRANS", pks: ["INT_UI", "DATETO", "TIMETO"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EVBS", pks: ["VSTELLE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_EWMOBJINSP", pks: ["OBJNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_FKKVKP", pks: ["VKONT", "GPART"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_IFLOT", pks: ["TPLNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ILOA", pks: ["ILOAN"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_INET", pks: ["KANTE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_KONV", pks: ["KNUMV", "KPOSN", "STUNR", "ZAEHK"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_KSSK", pks: ["OBJEK", "MAFID", "KLART", "CLINT", "ADZHL"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_LFA1", pks: ["LIFNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_MAKT", pks: ["MATNR", "SPRAS"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_MBEWH", pks: ["MATNR", "BWKEY", "BWTAR", "LFGJA", "LFMON"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_MKPF", pks: ["MBLNR", "MJAHR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_MLST", pks: ["MLST_ZAEHL", "ZAEHL"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_MLTX", pks: ["MLTX_ZAEHL", "LANGU", "AEND_ZAEHL"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_MSEG", pks: ["MBLNR", "MJAHR", "ZEILE"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_PMSDO", pks: ["OBJNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_PRPS", pks: ["PSPNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_QMEL", pks: ["QMNUM"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_QMFE", pks: ["QMNUM", "FENUM"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_QMIH", pks: ["QMNUM"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_QMMA", pks: ["QMNUM", "MANUM"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_RESB", pks: ["RSNUM", "RSPOS", "RSART"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_RKPF", pks: ["RSNUM"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_SWWWIHEAD", pks: ["WI_ID"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_VBAK", pks: ["VBELN"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_VBFA", pks: ["VBELV", "POSNV", "VBELN", "POSNN", "VBTYP_N"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_VBRK", pks: ["VBELN"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_VBRP", pks: ["VBELN", "POSNR"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" },
    { nombre: "Z_ZAVISOS_ZG", pks: ["QMNUM"], campoFecha: "GLCHANGETIME", campoBorrado: "GLDELFLAG" }
   */

  /*{
    nombre: "NOMBRE_TABLA",
    pks: ["PRIMARY_KEYS", ""],
    campoFecha: "COLUMNA_FECHA",
    campoBorrado: "COLUMNA_BORRADOR",
   } */
];

const SOURCE_PROJECT = "integracion-snp-glue";     
const SOURCE_DATASET = "MRP_STANDARD";
const TARGET_DATASET = "MRP_STANDARD"; 

tablasSAP.forEach((tabla) => {

    operate(tabla.nombre, {
        dataset: TARGET_DATASET,
        tags: ["sap_mantenimiento_diario"],
        hasOutput: true // para que Dataform no modifique la tabla, que ya existe
    })
    .queries((ctx) => {
        const campoBorrado = tabla.campoBorrado                                 // Validamos si la tabla tiene un campo de borrado definido
        ? `source.${tabla.campoBorrado}`                                        // Si lo tiene, apuntamos a la columna original
        : `CAST(NULL AS STRING)`;                                               // Si no lo tiene, inyectamos un NULL simulado para que no se rompa el MERGE

    return `

        BEGIN                                                                                        -- Creamos variables vacías para guardar el texto que vamos a generar

            DECLARE columnas_update STRING;
            DECLARE script_merge STRING;

            -- 1. Leemos automáticamente todas las columnas de la tabla para el UPDATE

                SET columnas_update = (
                SELECT STRING_AGG('target.' || column_name || ' = source.' || column_name, ', ')
                FROM \`${SOURCE_PROJECT}.${SOURCE_DATASET}.INFORMATION_SCHEMA.COLUMNS\`
                WHERE table_name = '${tabla.nombre}'
            );

            -- 2. Montamos el merge, inyectando las columnas completas

            SET script_merge = CONCAT(
                'MERGE ${ctx.self()} AS target ',
                
                -- Solo deja pasar la version más reciente de cada PK

                'USING ( ',                                                                                 -- se lee los datos raw

                    'SELECT * FROM \`${SOURCE_PROJECT}.${SOURCE_DATASET}.${tabla.nombre}\` ',
                    'QUALIFY ROW_NUMBER() OVER ( ',
                        'PARTITION BY ${tabla.pks.join(", ")} ',
                        'ORDER BY ${tabla.campoFecha} DESC ',
                    ') = 1 ',
                ') AS source ',                                                                     -- conjunto de dados numerados y unicos
            
                'ON ${tabla.pks.map(pk => `target.${pk} = source.${pk}`).join(" AND ")} ',          -- Conecta la fila que llega de SAP con la que existe, uniendo todas sus PKs  

                'WHEN MATCHED AND IFNULL(${campoBorrado}, \\'\\') != \\'\\' THEN ',    -- Regla DELETED
                    'DELETE ',

                'WHEN MATCHED AND IFNULL(${campoBorrado}, \\'\\') = \\'\\' THEN ',     -- Regla MODIFIED , hace el update de la línea si no tiene el flag borrador. Mismo que no tenga cambios.
                    'UPDATE SET ', columnas_update, ' ',

                'WHEN NOT MATCHED AND IFNULL(${campoBorrado}, \\'\\') = \\'\\' THEN ', -- Regla AÑADIR
                    'INSERT ROW'
            );

            EXECUTE IMMEDIATE script_merge;
        END;
       `;
    });  
});          