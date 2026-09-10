-- Isolated regression model of GIANTS' post-prediction veto and timed engagement.
-- Does not simulate tyres, terrain, rendering or the FS25 engine.
local root = arg and arg[1] or "."
local passed = 0
local function check(value, message) assert(value, message); passed=passed+1 end
math.clamp = function(v,a,b) return math.max(a,math.min(v,b)) end
local logs
local function boot(diagnostics)
    g_time=10000; g_currentModDirectory='/test/c330/'
    C330Runtime=nil; C330TransmissionFix=nil; C330TransmissionWorkFix=nil; C330FullDiagnostic=nil
    logs={}
    Logging={info=function(format,...) logs[#logs+1]=string.format(format,...) end,
        warning=function(format,...) logs[#logs+1]='WARNING '..string.format(format,...) end}
    addModEventListener=function() end
    ConfigurationUtil={getXMLConfigurationKey=function() return 'motor' end}
    Vehicle={update=function(self,dt) self.originalUpdated=true; return 'vehicle-result' end}
    VehicleMotor={SHIFT_MODE_AUTOMATIC=1}
    VehicleMotor.getBestStartGear=function() return 1,1 end
    VehicleMotor.getUseAutomaticGroupShifting=function() return true end
    VehicleMotor.findGearChangeTargetGearPrediction=function(m,cur) return m.nativeTarget or cur end
    VehicleMotor.setGearGroup=function(m,range) m.activeGearGroupIndex=range; m.groupChangeTimer=500; m.gear=0 end
    VehicleMotor.setGear=function(m,gear) m.targetGear=gear; m.gear=0; m.gearChangeTimer=400 end
    VehicleMotor.updateGear=function(m,accel,brake,dt)
        m.lastAcceleratorPedal=accel
        if m.gearChangeTimer>=0 then
            m.gearChangeTimer=m.gearChangeTimer-dt
            m.groupChangeTimer=math.max(-1,m.groupChangeTimer-dt)
            if m.gearChangeTimer<0 then m.gear=m.targetGear; m.allowGearChangeTimer=3000; m.allowGearChangeDirection=m.targetGear>m.previousGear and 1 or -1 end
        elseif m.groupChangeTimer>0 then m.groupChangeTimer=m.groupChangeTimer-dt
        else
            local oldRange=m.activeGearGroupIndex
            local new=m:findGearChangeTargetGearPrediction(m.gear,{{},{},{}},1,0,accel,dt)
            m.allowGearChangeTimer=m.allowGearChangeTimer-dt
            if m.allowGearChangeTimer>0 and accel>0 and new<m.gear and m.allowGearChangeDirection~= -1 then new=m.gear end
            if new~=m.gear or oldRange~=m.activeGearGroupIndex then
                m.previousGear=m.gear; m.targetGear=new; m.gear=0; m.gearChangeTimer=400
            end
        end
        -- Distinct adjusted brake detects dropped results and input-brake substitution.
        return 0.42, m.testAdjustedBrake or 0.73
    end
    dofile(root..'/Scripts/C330Runtime.lua')
    dofile(root..'/Scripts/C330TransmissionFix.lua')
    dofile(root..'/Scripts/C330TransmissionWorkFix.lua')
    C330TransmissionWorkFix:install()
    if diagnostics then dofile(root..'/Scripts/C330FullDiagnostic.lua'); C330FullDiagnostic:install() end
end
local function make(v)
    v=v or {}
    local vehicle={configFileName='/test/c330/c330m.xml',isServer=true,isClient=true,configurations={motor=1}}
    vehicle.xmlFile={getValue=function() return v.model or 'C-330' end}
    vehicle.getLastSpeed=function() return v.speed or 7.2 end
    vehicle.getTotalMass=function() return 2.5 end
    vehicle.getSpeedLimit=function(_,tools) return tools and (v.limit or math.huge) or math.huge,true end
    vehicle.getAttachedImplements=function() return {} end
    vehicle.getIsMotorStarted=function() return v.started~=false end
    vehicle.getIsActive=function() return true end
    vehicle.getDamageAmount=function() return 0 end
    if v.ads~=nil then vehicle.spec_AdvancedDamageSystem={dynamicMotorLoad=v.ads} end
    local m=setmetatable({vehicle=vehicle,gear=v.gear or 1,targetGear=v.gear or 1,activeGearGroupIndex=v.range or 2,
        gearGroups={{},{}},gearShiftMode=v.manual and 2 or 1,currentDirection=v.reverse and -1 or 1,
        autoGearChangeTime=300,autoGearChangeTimer=0,allowGearChangeTimer=2500,allowGearChangeDirection=1,
        gearChangeTimer=-1,groupChangeTimer=-1,directionChangeTimer=-1,lastAcceleratorPedal=1,nativeTarget=v.target,
        c330FixSettledGearSince=0}, {__index=VehicleMotor})
    m.c330FixSettledGearKey=string.format('%d:%d:%d',m.currentDirection,m.activeGearGroupIndex,m.gear)
    m.getLastModulatedMotorRpm=function() return v.rpm or 2200 end
    m.getSmoothLoadPercentage=function() return v.native or 0.3 end
    m.getTorqueCurveValue=function(_,rpm) return rpm<1500 and 0.1 or 0.087 end
    vehicle.spec_motorized={motor=m,exhaustEffects={}}
    vehicle.spec_wheels={wheels={}}
    for i=1,4 do vehicle.spec_wheels.wheels[i]={additionalMass=0.204,radius=0.6,
        physics={wheelShapeCreated=true,contact=1,hasGroundContact=true,restLoad=0.7,
        netInfo={slip=v.slip or 0.1,xDriveSpeed=4,suspensionLength=0.2},getTireLoad=function() return 0.72,true end}} end
    return m,vehicle,v
end
local function predict(m) return m:findGearChangeTargetGearPrediction(m.gear,{{},{},{}},1,0,1,16) end
local function tick(m,ms) g_time=g_time+(ms or 100); return m:updateGear(1,0,ms or 100) end
local function ticks(m,n) for i=1,n do tick(m,100) end end
boot(true)
local m,v,values=make({gear=2,range=2,rpm=1023,ads=0.876,limit=15,speed=3.58,target=3})
check(tick(m)==0.42,'preserve updateGear return')
check(m.gear==0 and m.targetGear==1,'P1 replay: rescue beats native upshift/ceiling and bypasses 3s veto')
check(m.gearChangeTimer==400,'mechanical clutch/gear time retained')
check(m.c330P2.vetoBefore==2500,'capture veto before release')
ticks(m,5)
check(m.gear==1,'requested rescue actually engages')
check(m.c330P2.reductionCompletedAt-m.c330P2.reductionRequestedAt<=600,'rescue engagement latency bounded by model clutch time')
C330FullDiagnostic:update(16)
local log=table.concat(logs,'\n')
check(log:find('SHIFT_ACTUAL') and log:find('tireLoadT=0.720',1,true),'actual transitions and correct tire load API logged')
check(log:find('allowTimerMs=') and log:find('reductionCompletedMs=500',1,true),'execution timers and latency logged')
check(not log:find('disabled for one tractor',1,true),'diagnostic accepts multi-return speed/force methods')
local serial=m.c330FullDiagTransitionSeq
check(serial>=2,'disengagement and engagement both captured between snapshots')
-- Diagnostic probes cannot abort the driving call.
v.getAttachedImplements=function() error('probe failure') end
check(tick(m)==0.42,'broken diagnostic getter cannot interrupt drivetrain')
C330FullDiagnostic:update(16)
boot(false)
local high=make({gear=1,range=2,rpm=2194,ads=0.788,limit=15,target=2})
check(predict(high)==1 and high.c330P2.gate=='TORQUE RESERVE','P1 replay: II/2 rejected when predicted demand exceeds reserve')
local fast=make({gear=3,range=2,rpm=2200,limit=8.4,speed=22.878,target=3})
check(predict(fast)==3 and fast.c330P2.reason=='DOWNSHIFT RPM GUARD','lowering tool at road speed cannot force overspeed')
local low=make({gear=3,range=1,rpm=2200,limit=3,speed=5.6,target=3})
low.c330FixRangeRecoverySince=0
check(predict(low)==3 and low.activeGearGroupIndex==1,'base controller cannot bypass low work ceiling')
local free=make({gear=1,range=2,ads=0.2,limit=15,target=2})
ticks(free,32)
check(free.gear==2,'II/2 remains attainable with torque reserve (no blanket 1500rpm floor)')
local slip=make({gear=1,range=2,ads=0.2,limit=15,target=2,slip=0.6})
ticks(slip,32)
check(slip.gear==1,'wheelspin is not treated as readiness for higher gear')
-- A failed range change is remembered while load remains unchanged.
local hunt,hv,h=make({gear=3,range=1,rpm=2200,ads=0.65,limit=15,speed=5.4,target=3})
ticks(hunt,32)
check(hunt.gear==1 and hunt.activeGearGroupIndex==2,'loaded I/3 to II/1 is attainable')
h.rpm=1300;h.speed=4.5;hv.spec_AdvancedDamageSystem.dynamicMotorLoad=0.70;hunt.nativeTarget=1
tick(hunt)
check(hunt.c330P2.failure and hunt.c330P2.failure.to==4,'failure recorded before clutch unloading masks load')
ticks(hunt,6)
h.rpm=2200;h.speed=5.4;hv.spec_AdvancedDamageSystem.dynamicMotorLoad=0.65;hunt.nativeTarget=3
ticks(hunt,90)
check(hunt.gear==3 and hunt.activeGearGroupIndex==1,'time alone does not retry failed range')
hv.spec_AdvancedDamageSystem.dynamicMotorLoad=0.30
ticks(hunt,30)
check(hunt.activeGearGroupIndex==2,'sustained load improvement unlocks retry')
-- Optional integration and isolation.
local bare=make({limit=8.4,target=2})
check(predict(bare)==1 and bare.c330WorkLoadSource=='GIANTS','no ADS fallback')
local overload=make({ads=1.3,native=0.2,gear=2,rpm=1100,limit=15})
check(predict(overload)==1 and overload.c330WorkLoadSource=='ADS','valid ADS overload must not fall back to low native load')
for _,bad in ipairs({-0.1,math.huge,0/0}) do
    local invalid=make({ads=bad,native=0.4})
    local load,sourceName=C330Runtime.load(invalid)
    check(load==0.4 and sourceName=='GIANTS','invalid ADS fallback')
end
local manual=make({manual=true,target=2})
check(predict(manual)==2 and manual.allowGearChangeTimer==2500 and manual.c330P2==nil,'manual isolation')
local other=make({target=2,limit=8.4});other.vehicle.configFileName='/other/c330m.xml'
check(predict(other)==2 and other.c330P2==nil,'other mods isolation')
local reverse=make({reverse=true,gear=1,range=1,target=1})
predict(reverse);check(reverse.c330P2==nil,'P2 forward rules do not alter reverse controller')
local cm=make({model='C-330M',limit=8.4,target=2})
check(predict(cm)==1,'C330M work ceiling supported')
-- Queue capacity reports missing events instead of silently losing transitions.
boot(true)
local queued=make({manual=true})
for i=1,140 do queued.gear=i%2+1; queued.targetGear=queued.gear; queued.nativeTarget=3-queued.gear; queued.gearChangeTimer=-1; queued.allowGearChangeTimer=0;tick(queued) end
check((queued.c330FullDiagDropped or 0)>0,'bounded queue reports overflow')
C330FullDiagnostic:update(16)
check(table.concat(logs,'\n'):find('EVENT_OVERFLOW',1,true)~=nil,'overflow reaches log')
-- A future formatting/probe bug disables diagnostics once, never updateGear.
local originalFlush=C330FullDiagnostic.flushMotor
C330FullDiagnostic.flushMotor=function() error('simulated deferred probe bug') end
g_time=g_time+300;C330FullDiagnostic:update(16)
check(queued.c330FullDiagDisabled==true,'deferred diagnostic failure is isolated')
local count=#logs
g_time=g_time+300;C330FullDiagnostic:update(16)
check(#logs==count,'disabled diagnostic does not spam errors')
check(tick(queued)==0.42,'drivetrain still runs after diagnostic shutdown')
C330FullDiagnostic.flushMotor=originalFlush
-- P4: two-return contract, with and without the diagnostic wrapper, including
-- paths that bypass the automatic-forward controller and unrelated vehicles.
for _, diagnostics in ipairs({false, true}) do
    for _, mode in ipairs({'automatic', 'manual', 'reverse', 'client', 'other'}) do
        for _, brake in ipairs({0, 0.73, 1}) do
            boot(diagnostics)
            local motor, vehicle = make({manual=mode=='manual', reverse=mode=='reverse'})
            if mode=='client' then vehicle.isServer=false end
            if mode=='other' then vehicle.configFileName='/other/tractor.xml' end
            motor.testAdjustedBrake=brake
            local accelerator, adjustedBrake=tick(motor)
            check(accelerator==0.42 and adjustedBrake==brake,
                'both adjusted pedals preserved: '..mode..' diagnostics='..tostring(diagnostics))
            local automaticBrake=false
            local brakeLights=not automaticBrake and math.abs(adjustedBrake)>0
            check(brakeLights==(brake>0),'Lights brake expression receives numeric pedal')
        end
    end
end
-- P5 replay: unloaded top-gear request at ~960 RPM must be rejected.
boot(false)
local roadLow=make({model='C-330M',gear=2,range=2,rpm=960.4,ads=0.436,speed=10,target=3})
check(predict(roadLow)==2,'road upshift cannot bypass low RPM gate')
check(roadLow.c330P2.gate=='UPSHIFT RPM','road upshift evaluated by common gate')
-- Replay the later healthy II/2 run: old absolute load delta is NOT required
-- when the road retry has adequate current torque reserve and postshift RPM.
local function failedRoad(load,limit)
    local m=make({model='C-330M',gear=2,range=2,rpm=2230.7,ads=load,speed=16.493,target=3,limit=limit})
    predict(m)
    m.c330P2.failure={to=6,load=0.436,speed=10,at=g_time-6000}
    return m
end
local retry=failedRoad(0.343)
predict(retry)
check(retry.c330P2.gate=='STABILIZING','healthy road retry starts sustained observation')
ticks(retry,10)
check(retry.gear==2 and retry.targetGear==2,'retry cannot engage before 2s stability')
ticks(retry,16)
check(retry.gear==3,'healthy road retry reaches II/3 despite old absolute load threshold')
local risky=failedRoad(0.8)
ticks(risky,80)
check(risky.gear==2,'time alone cannot unlock overloaded road retry')
-- Realistic II/1 work case from C-330 dry-soil log remains protected.
local work=make({gear=1,range=2,rpm=2222.7,ads=0.561,speed=7.445,limit=15,target=2})
ticks(work,35)
check(work.gear==1 and work.c330P2.gate=='TORQUE RESERVE','P5 does not relax working torque reserve')
-- Two simultaneously present tractors must have independent failure memories.
local clear=make({model='C-330',gear=2,range=2,rpm=2200,ads=0.2,speed=14.3,target=3})
predict(clear)
check(clear.c330P2.failure==nil and risky.c330P2.failure.to==6,'failed gear memory is per motor')
print(string.format('PASS: %d regression assertions (isolated GIANTS contract model; game test still required)',passed))
