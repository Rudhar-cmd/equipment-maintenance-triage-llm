export function runThresholdChecks(readings=[]) {
  const r=Object.fromEntries(readings.map(x=>[x.name,x]));
  return [
    {rule:"MOTOR_TEMP_HIGH",triggered:typeof r.temperature?.value==="number"&&r.temperature.value>90,message:typeof r.temperature?.value==="number"?`Temperature ${r.temperature.value}°C; threshold is 90°C.`:"Temperature reading was not supplied."},
    {rule:"VIBRATION_HIGH",triggered:typeof r.vibration?.value==="number"&&r.vibration.value>7,message:typeof r.vibration?.value==="number"?`Vibration ${r.vibration.value} mm/s; threshold is 7 mm/s.`:"Vibration reading was not supplied."}
  ];
}
export function detectConflicts(readings=[]) {
  const out=[];
  for(const name of ["temperature","vibration"]){
    const vals=readings.filter(x=>x.name===name).map(x=>x.value);
    if(vals.length>1&&vals.some(v=>Math.abs(v-vals[0])>.001)) out.push({sensor:name,readings:vals,message:`Conflicting ${name} readings require technician verification.`});
  }
  return out;
}
