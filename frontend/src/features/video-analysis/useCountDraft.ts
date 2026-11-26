import {useEffect,useState} from 'react';import type {LineWrite} from './countLinesContracts';
export type CountDraft={lines:LineWrite[]};
export function useCountDraft(file:File|undefined){
 const [firstFrame,setFirstFrame]=useState<HTMLCanvasElement>(),[draft,setDraft]=useState<CountDraft>();
 useEffect(()=>{
  setFirstFrame(undefined);setDraft(undefined);if(!file)return;
  let live=true;const video=document.createElement('video'),url=URL.createObjectURL(file);video.muted=true;video.preload='auto';
  video.onloadeddata=()=>{if(!live||!video.videoWidth)return;video.pause();const canvas=document.createElement('canvas');canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d')?.drawImage(video,0,0);setFirstFrame(canvas)};video.src=url;
  return()=>{live=false;video.onloadeddata=null;video.pause();video.removeAttribute('src');video.load();URL.revokeObjectURL(url)};
 },[file]);
 return {firstFrame,draft,setDraft};
}
