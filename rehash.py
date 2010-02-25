def main(instance, world, sonic) :
    loggedin = world.instances[instance].loggedin
    sock = world.instances[instance].sock
    address = world.instances[instance].address
    bufferbackup = world.instances[instance].buffer
    status = world.instances[instance].status
    oper = world.instances[instance].oper
    operlevel = world.instances[instance].operlevel
    loggedinas = world.instances[instance].loggedinas
    del world.instances[instance]
    newinstance = sonic
    newinstance.loggedin = loggedin
    newinstance.sock = sock
    newinstance.address = address
    newinstance.buffer = bufferbackup
    newinstance.status = status
    newinstance.oper = oper
    newinstance.operlevel = operlevel
    newinstance.loggedinas = loggedinas
    world.instances[instance] = newinstance
