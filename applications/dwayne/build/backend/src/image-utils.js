import imageDataURI from "image-data-uri"
import tempfile from "tempfile";
import {thumbnail} from "easyimage"
import https from "https"
import {readChunk} from 'read-chunk';
import imageType, {minimumBytes} from 'image-type';
import fsp from 'fs/promises'
import fs from "fs"
import fetch from 'node-fetch';
import { Readable } from 'stream'
import { finished } from 'stream/promises';


import util from 'util'
import {pipeline}  from "stream/promises"
import mime from 'mime-types'

async function download(url, dest) {
  let response = await fetch(url, {timeout:2000})
  if (!response.ok) throw new Error(`unexpected response ${response.statusText}`)
  let type = response.headers.get('Content-Type')
  await pipeline(response.body, fs.createWriteStream(`${dest}.${mime.extension(type)}`))
  return `${dest}.${mime.extension(type)}`
}



export async function handleThumbnail(url) {
    try {
        let src = tempfile()
        src = await download(url, src);
        const thumbnailInfo = await thumbnail({
            src: src,
            width: 100,
            height: 100,
        });
        return await imageDataURI.encodeFromFile(thumbnailInfo.path);
    } catch (err) {
        console.log(err);
        return null;
    }
}