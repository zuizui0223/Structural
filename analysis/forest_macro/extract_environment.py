"""Join 2021 WorldCover to forest plots, with dated buffers and uncertainty.
Tree-cover class fractions are NOT canopy closure or native-forest cover.
No species, abundances or biodiversity outcomes are read.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import defaultdict
import numpy as np
import rasterio
from rasterio.windows import from_bounds,Window

def tile_name(lat,lon):
 a=3*math.floor(lat/3);b=3*math.floor(lon/3)
 return f'{"N" if a>=0 else "S"}{abs(a):02d}{"E" if b>=0 else "W"}{abs(b):03d}'
def cover_stats(a,mask,w):
 valid=mask&(a!=0);total=float(w[mask].sum());den=float(w[valid].sum())
 out={'pixel_n':int(mask.sum()),'valid_pixel_n':int(valid.sum()),'valid_fraction':den/total if total else 0}
 for key,classes in [('tree_cover_class_fraction',[10]),('shrubland_class_fraction',[20]),('tree_plus_shrub_class_fraction',[10,20]),('water_class_fraction',[80])]:
  out[key]=float(w[valid&np.isin(a,classes)].sum()/den) if den else None
 return out
def csvout(p,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
def run(ledger,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);patches=out/'worldcover_patches';patches.mkdir(exist_ok=True)
 with Path(ledger).open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 groups=defaultdict(list)
 for r in rows:groups[tile_name(float(r['latitude']),float(r['longitude']))].append(r)
 results=[];sources=[];errors=[]
 with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='45',GDAL_HTTP_MAX_RETRY='1'):
  for tile,plots in sorted(groups.items()):
   url=f'https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
   try:
    with rasterio.open(url) as ds:
     sources.append({'tile':tile,'url':url,'crs':str(ds.crs),'resolution_degrees':list(ds.res),'year':2021,'version':'v200'})
     cache={}
     for r in plots:
      key=(float(r['latitude']),float(r['longitude']))
      if key not in cache:
       lat,lon=key;dy=1100/111195;dx=dy/math.cos(math.radians(lat))
       win=from_bounds(lon-dx,lat-dy,lon+dx,lat+dy,ds.transform)
       win=Window(math.floor(win.col_off),math.floor(win.row_off),math.ceil(win.width)+2,math.ceil(win.height)+2)
       if win.col_off<0 or win.row_off<0 or win.col_off+win.width>ds.width or win.row_off+win.height>ds.height:raise ValueError('Buffer crosses tile edge; mosaic required')
       a=ds.read(1,window=win);tr=ds.window_transform(win)
       iy,ix=np.indices(a.shape);yy=tr.f+(iy+.5)*tr.e;xx=tr.c+(ix+.5)*tr.a
       east=(xx-lon)*111195*np.cos(np.radians(lat));north=(yy-lat)*111195;dist=np.hypot(east,north);weights=np.cos(np.radians(yy))
       result={'extraction_status':'ok','environment_year':2021,'environment_product':'ESA_WorldCover_2021_v200','tile':tile}
       for radius in (100,500,1000):
        for k,v in cover_stats(a,dist<=radius,weights).items():result[f'{k}_{radius}m']=v
       vals=[]
       for angle in range(0,360,45):
        dd=np.hypot(east-45*math.cos(math.radians(angle)),north-45*math.sin(math.radians(angle)))
        vals.append(cover_stats(a,dd<=500,weights)['tree_cover_class_fraction'])
       validvals=[v for v in vals if v is not None]
       result['tree_cover_500m_45m_offset_min']=min(validvals) if validvals else None;result['tree_cover_500m_45m_offset_max']=max(validvals) if validvals else None
       patch=patches/(hashlib.sha256(f'{lat:.8f}|{lon:.8f}'.encode()).hexdigest()[:16]+'.tif')
       with rasterio.open(patch,'w',driver='GTiff',height=a.shape[0],width=a.shape[1],count=1,dtype=a.dtype,crs=ds.crs,transform=tr,nodata=0,compress='deflate') as dst:dst.write(a,1)
       result['patch_file']=str(patch.relative_to(out));result['patch_sha256']=hashlib.sha256(patch.read_bytes()).hexdigest();cache[key]=result
      years=[int(y) for y in r['years'].split('|') if y.isdigit()]
      results.append({**r,**cache[key],'nearest_sampling_year_gap_to_2021':min(abs(y-2021) for y in years) if years else None,'has_2019_2022_sampling':any(2019<=y<=2022 for y in years)})
     print(tile,len(plots),'plot records',len(cache),'coordinate windows',flush=True)
   except Exception as e:
    errors.append({'tile':tile,'error':str(e),'url':url})
    completed={x['plot_key'] for x in results}
    for r in plots:
     if r['plot_key'] not in completed:results.append({**r,'extraction_status':'error','environment_year':2021,'tile':tile,'error':str(e)})
 csvout(out/'forest_plot_environment_2021.csv',results)
 report={'input_plot_records':len(rows),'success_plot_records':sum(r['extraction_status']=='ok' for r in results),'sources':sources,'errors':errors,'method':'Local equirectangular radius in metres, cos(latitude) area weights; nodata excluded, water retained and reported. 100/500/1000m buffers; 8 offsets at 45m are positional sensitivity, not confidence intervals.','limitations':['2021 snapshot only; do not backcast to early BALA campaigns','Tree-cover classified area is not canopy closure, tree height, native forest or biological forest quality','Tree plus shrub is separate sensitivity, not a validated native-forest definition','Original coordinates have 45m reported uncertainty; shared site IDs and co-location require clustering review'],'ecological_outcome_rows_read':0,'sha256_output':hashlib.sha256((out/'forest_plot_environment_2021.csv').read_bytes()).hexdigest()}
 (out/'environment_provenance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ledger',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.ledger,a.out)
