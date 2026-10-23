  // Diagnostic scheduling: place the one original readonly measurement just
  // before a real native-dispatched restore callback. Never move its callback
  // to another task, invoke it by hand, or write a DOM coordinate/scroll/value.
  let pendingMeasure=null, targetedRaf=null, activeRender=null;
  const originalRaf=window.requestAnimationFrame, originalCancelRaf=window.cancelAnimationFrame;
  const originalRafSource=Function.prototype.toString.call(originalRaf),originalCancelRafSource=Function.prototype.toString.call(originalCancelRaf);
  const integrity=message=>errors.push(message);
  const safeObserve=(kind,extra)=>{try{append(kind,{...extra,state:state()});}catch(error){integrity('Native rAF observation failed: '+String(error?.stack||error));}};
  function rejectPending(error){
    const pending=pendingMeasure;
    if(!pending)return;
    pendingMeasure=null;clearTimeout(pending.timer);pending.reject(error);
  }
  function completeNativeControl(p,before,callbackThis,callbackArgs){
    const ratio=document.getElementById('refGuideRatio'),label=ratio?.closest('label'),hit=document.elementFromPoint(p.x,p.y);
    controlled.original_measure=p;controlled.old_center={x:p.x,y:p.y};
    controlled.before=before;controlled.after={...compact('#refGuideMode',p),hitAtOldPoint:desc(hit)};
    controlled.after_state=state();controlled.target_label=desc(label);controlled.after_hit=desc(hit);
    controlled.returned_response_json=JSON.stringify(heldQuery.result);
    controlled.parsed_json_unchanged=controlled.returned_response_json===controlled.original_response_json;
    controlled.response_scope='Same apiRequest return object and serialized parsed JSON; not HTTP wire bytes.';
    controlled.native_callback={native_id:targetedRaf.id,registration_stack:targetedRaf.stack,callback_source:targetedRaf.source,
      original_request_animation_frame_source:originalRafSource,original_cancel_animation_frame_source:originalCancelRafSource,
      original_request_animation_frame_native:originalRafSource.includes('[native code]'),original_cancel_animation_frame_native:originalCancelRafSource.includes('[native code]'),
      callback_source_matches:true,renderer:targetedRaf.renderer,native_dispatch_count:targetedRaf.dispatches,
      this_is_window:callbackThis===window,native_args:Array.from(callbackArgs),cancelled:targetedRaf.cancelled,
      original_measure_evaluations:targetedRaf.measureEvaluations,callback_completed:true};
    controlled.valid=!!p.hit&&before.hit?.id==='refGuideMode'&&
      before.nodeToken===controlled.after.nodeToken&&!!label&&(hit===label||hit===ratio)&&
      controlled.parsed_json_unchanged&&targetedRaf.dispatches===1&&targetedRaf.measureEvaluations===1&&
      !targetedRaf.cancelled&&ReferenceWorkspace.context()===heldQuery.context&&heldQuery.arm_token===armedToken;
    controlled.count=1;controlled.applied=controlled.valid;
    if(!controlled.valid)controlled.error='Original native scroll restore did not produce the declared mode-to-ratio displacement';
    trace.gate=publicControl();
    append('controlled-native-raf-measurement',{control:publicControl(),state:state()});
    return controlled.valid;
  }
  const rafWrapper=function(callback,...otherArgs){
    if(!pendingMeasure||!activeRender?.matching)
      return Reflect.apply(originalRaf,this,[callback,...otherArgs]);
    let stack='';
    try{stack=String(new Error('P88 native rAF registration').stack||'');}catch(error){integrity(String(error));}
    const atRestore=stack.includes('/app.js:'+restoreRafLine+':');
    if(!atRestore)
      return Reflect.apply(originalRaf,this,[callback,...otherArgs]);
    let sourceText='';
    try{sourceText=Function.prototype.toString.call(callback);}catch(error){integrity(String(error));}
    if(targetedRaf||sourceText!==restoreCallbackSource){
      integrity(targetedRaf?'More than one eligible original restore callback':'Original restore callback bytes do not match pinned F');
      rejectPending(Error('P88 native rAF schedule precondition: callback identity is not unique'));
      return Reflect.apply(originalRaf,this,[callback,...otherArgs]);
    }
    const target=targetedRaf={id:null,source:sourceText,stack,renderer:activeRender.invocation,dispatches:0,measureEvaluations:0,cancelled:false};
    const nativeWrapper=function(...nativeArgs){
      target.dispatches++;
      const pending=pendingMeasure;
      // If an earlier timeout/cancel invalidated the proof, the real callback
      // still keeps its native dispatch and original exception semantics.
      if(!pending)return Reflect.apply(callback,this,nativeArgs);
      let measured,measureError,measureThrew=false,callbackResult,callbackError,callbackThrew=false,before=null;
      safeObserve('native-restore-entry',{native_id:target.id,renderer:target.renderer,native_args:nativeArgs,this_is_window:this===window});
      try{
        if(target.dispatches!==1||ReferenceWorkspace.context()!==heldQuery.context||heldQuery.arm_token!==armedToken)
          throw Error('P88 native rAF schedule precondition: dispatch/context changed');
        target.measureEvaluations++;measured=Reflect.apply(pending.evaluate,undefined,[]);
        before=compact('#refGuideMode',measured);
        append('measure',{selector:'#refGuideMode',original_measure:measured,hit_at_return:desc(document.elementFromPoint(measured.x,measured.y)),state:state(),inside_native_restore_before_original:true});
      }catch(error){measureError=error;measureThrew=true;}
      // The original callback always executes exactly here, even if the
      // diagnostic's read/observer failed. Original throw has priority.
      try{callbackResult=Reflect.apply(callback,this,nativeArgs);}
      catch(error){callbackError=error;callbackThrew=true;}
      safeObserve('native-restore-return',{native_id:target.id,renderer:target.renderer,original_threw:callbackThrew});
      try{
        if(callbackThrew)throw Error('P88 native rAF schedule invalid: original callback threw');
        if(measureThrew)throw measureError;
        if(!completeNativeControl(measured,before,this,nativeArgs))
          throw Error('P88 original native restore did not reproduce the declared wrong-target displacement; not valid counterevidence');
        pendingMeasure=null;clearTimeout(pending.timer);pending.resolve(measured);
      }catch(error){rejectPending(error);}
      if(callbackThrew)throw callbackError;
      return callbackResult;
    };
    target.id=Reflect.apply(originalRaf,this,[nativeWrapper,...otherArgs]);
    safeObserve('native-restore-registered',{native_id:target.id,renderer:target.renderer,registration_stack:stack,callback_source_matches:true});
    return target.id;
  };
  const cancelRafWrapper=function(id,...args){
    if(targetedRaf&&targetedRaf.id===id&&pendingMeasure){
      targetedRaf.cancelled=true;safeObserve('native-restore-cancelled',{native_id:id});
      rejectPending(Error('P88 native rAF schedule precondition: original restore was cancelled'));
    }
    return Reflect.apply(originalCancelRaf,this,[id,...args]);
  };
  window.requestAnimationFrame=rafWrapper;window.cancelAnimationFrame=cancelRafWrapper;
  function measureWithRestore(selector,evaluate,measurementId){
    const guides=typeof fe==='undefined'?[]:fe.guides||[];
    const eligible=proofMode==='controlled'&&!controlled&&selector==='#refGuideMode'&&innerWidth===390&&
      guides.some(g=>typeof g.expression==='string'&&g.expression.startsWith('gridrule:'));
    if(!eligible){const p=Reflect.apply(evaluate,undefined,[]);trace.afterMeasure(selector,p);return p;}
    controlled={name:'P88-measure-before-original-native-restore',attempted:true,applied:false,valid:false,count:0,
      measurement_id:measurementId,before_query:state(),before:null,after:null,original_measure:null};
    if(!heldQuery||heldQuery.released||heldQuery.context!==ReferenceWorkspace.context()||heldQuery.arm_token!==armedToken)
      throw Error('P88 native rAF schedule precondition: no original held query for the first eligible measurement');
    controlled.original_response_json=heldQuery.result_json;controlled.query_callsite_stack=heldQuery.callsite_stack;
    return new Promise((resolve,reject)=>{
      const pending=pendingMeasure={evaluate,resolve,reject,timer:null};
      pending.timer=setTimeout(()=>rejectPending(Error('P88 native rAF schedule precondition exhausted the original 25-second budget')),25000);
      heldQuery.released=true;append('query-response-release-before-original-measure',{state:state()});heldQuery.release();
    });
  }
