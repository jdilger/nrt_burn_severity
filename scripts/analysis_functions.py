import ee
import json

def nbr(image:ee.Image)-> ee.Image:
    return image.normalizedDifference(['nir','swir2']).multiply(1000)

def dnbr(pre:ee.Image, post : ee.Image)-> ee.Image:
    return pre.subtract(post)

def rdnbr(pre:ee.Image, nrt : ee.Image)-> ee.Image:
    pre_nbr = nbr(pre)
    ntr_nbr = nbr(nrt)
    denominator = pre_nbr.divide(1000).abs().sqrt()
    numerator = dnbr(pre_nbr,ntr_nbr)
    out = numerator.divide(denominator)

    return out.rename('RdNBR')

def miller_thresholds(rdnbr :ee.Image)-> ee.Image:
    '''generates miller thresholds from 0-3
    0 : #very low or unburned
    1 : low
    2 : moderate
    3 : high

    Args:
        rdnbr (ee.Image): Relative NBR img

    Returns:
        ee.Image: [description]
    '''

    serv = rdnbr.where(rdnbr.lte(69),0) \
            .where(rdnbr.gte(69).And(rdnbr.lte(315)),1) \
            .where(rdnbr.gt(315).And(rdnbr.lte(640)),2) \
            .where(rdnbr.gt(640),3).rename('MillersThresholds')
    
    return serv