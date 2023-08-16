import discord
from discord import app_commands
from discord.ext import commands
from youtube_dl import YoutubeDL

class music(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.is_playing = False
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.vc = ""
    

    #searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}
    

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            title = self.music_queue[0][0]['title']

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            #self.vc.disconnect()
            print("Tentei desconectar!")


    async def connect_to_channel(self):
        if len(self.music_queue) > 0:
            #try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.play_next()
        else:
            self.is_playing = False
            await self.vc.disconnect()


    @app_commands.command(name="hino",description="Tocarei um hino do youtube!")
    @app_commands.describe(
        buscar = "Insira o nome ou link da música no YouTube"
    )
    async def play(self, interaction:discord.Interaction, buscar:str):
        await interaction.response.defer(thinking=True)
        query = buscar
        
        try:
            voice_channel = interaction.user.voice.channel
        except:
        #if voice_channel is None:
            #you need to be connected so that the bot knows where to go
            embedvc = discord.Embed(
                colour= 1646116,#grey
                description = "**Me ajuda a te ajudar!**\n\nPra tocar uma música, primeiro se conecte a um canal de voz."
            )
            await interaction.followup.send(embed=embedvc)
            return
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                embedvc = discord.Embed(
                    colour= 12255232,#red
                    description = "**Esse aí não hitou nem na Indonésia.**\n\nExperimente pesquisar com outro nome para a Kinga tentar encontrar novamente!"
                )
                await interaction.followup.send(embed=embedvc)
            else:
                embedvc = discord.Embed(
                    colour= 32768,#green
                    description = f"Nossa, essa é um hino!\n\nVocê adicionou a música **{song['title']}** à fila!"
                )
                
                await interaction.followup.send(embed=embedvc)
                self.music_queue.append([song, voice_channel])
                
                if self.is_playing == False:
                    await self.connect_to_channel()


    @app_commands.command(name="fila", description="Exibe as músicas atuais na fila.")
    async def q(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += f'**{i+1} - **' + self.music_queue[i][0]['title'] + "\n"

        print(retval)
        if retval != "":
            embedvc = discord.Embed(
                colour= 12255232,
                description = f"{retval}"
            )
            await interaction.followup.send(embed=embedvc)
        else:
            embedvc = discord.Embed(
                colour= 1646116,
                description = 'Não existe nenhuma música na fila no momento.'
            )
            await interaction.followup.send(embed=embedvc)


    @app_commands.command(name="skip", description="Pula a música atual que está tocando.")
    @app_commands.default_permissions(manage_channels=True)
    async def pular(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        print("pular.self.vc: " + str(self.vc))
        print("pular.self.is_playing: " + str(self.is_playing))
        print("pular.len(self.music_queue): " + str(len(self.music_queue)))
        if self.vc != "" and self.vc and self.is_playing == True:
            self.vc.stop()
            #try to play next in the queue if it exists
            embedvc = discord.Embed(
                colour= 1646116,#ggrey
                description = f"**Essa era uma bomba mesmo...**\n\nVocê pulou essa música que estava difícil de engolir."
            )
            await interaction.followup.send(embed=embedvc)
            await self.connect_to_channel()
        else:
            embedvc = discord.Embed(
                colour= 1646116,#ggrey
                description = f"**Tá doida, minha velha?**\n\nNão há nenhuma música pra pular."
            )
            await interaction.followup.send(embed=embedvc)



    @pular.error #Erros para kick
    async def skip_error(self,interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, commands.MissingPermissions):
            embedvc = discord.Embed(
                colour= 12255232,
                description = f"**Sinto muito, rata velha.**\n\nMas você precisa da permissão \"Gerenciar canais\" para pular músicas."
            )
            await interaction.followup.send(embed=embedvc)     
        else:
            raise error
        

    @app_commands.command(name="kinga", description="Lista todos os comandos da Kinga.")
    async def help(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        helptxt = "`/kinga` - Veja esse guia!\n`/hino` - Tocarei um hino do youtube.\n`/skip` - Pule para a próxima música da fila.\n`/fila` - Veja a fila de músicas na Playlist."
        embedhelp = discord.Embed(
            colour = 1646116,#grey
            title=f'Comandos do {self.client.user.name}',
            description = helptxt
        )
        try:
            embedhelp.set_thumbnail(url=self.client.user.avatar.url)
        except:
            pass
        await interaction.followup.send(embed=embedhelp)


async def setup(client):
    await client.add_cog(music(client))
    