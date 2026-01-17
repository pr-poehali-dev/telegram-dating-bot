import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

type Profile = {
  id: number;
  name: string;
  age: number;
  city: string;
  gender: 'male' | 'female';
  photo: string;
  status: 'pending' | 'approved' | 'rejected';
  bio?: string;
};

type Match = {
  profileId: number;
  mutualLike: boolean;
  username?: string;
};

const Index = () => {
  const { toast } = useToast();
  const [view, setView] = useState<'onboarding' | 'main'>('onboarding');
  const [activeTab, setActiveTab] = useState('browse');
  
  const [myProfile, setMyProfile] = useState<Profile | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    city: '',
    gender: 'male' as 'male' | 'female',
    photo: '',
    bio: ''
  });

  const [currentProfileIndex, setCurrentProfileIndex] = useState(0);
  const [likesLeft, setLikesLeft] = useState(15);
  const [matches, setMatches] = useState<Match[]>([]);

  const sampleProfiles: Profile[] = [
    {
      id: 1,
      name: 'Алексей',
      age: 16,
      city: 'Москва',
      gender: 'male',
      photo: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex',
      status: 'approved',
      bio: 'Увлекаюсь программированием и музыкой'
    },
    {
      id: 2,
      name: 'Мария',
      age: 15,
      city: 'Санкт-Петербург',
      gender: 'female',
      photo: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Maria',
      status: 'approved',
      bio: 'Люблю рисовать и путешествовать'
    },
    {
      id: 3,
      name: 'Дмитрий',
      age: 17,
      city: 'Казань',
      gender: 'male',
      photo: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Dmitry',
      status: 'approved',
      bio: 'Занимаюсь спортом и фотографией'
    }
  ];

  const handleSubmitProfile = () => {
    if (!formData.name || !formData.age || !formData.city || !formData.photo) {
      toast({
        title: 'Ошибка',
        description: 'Заполните все обязательные поля',
        variant: 'destructive'
      });
      return;
    }

    const newProfile: Profile = {
      id: Date.now(),
      name: formData.name,
      age: parseInt(formData.age),
      city: formData.city,
      gender: formData.gender,
      photo: formData.photo,
      status: 'pending',
      bio: formData.bio
    };

    setMyProfile(newProfile);
    setView('main');
    
    toast({
      title: 'Анкета отправлена на модерацию',
      description: 'Администратор проверит её в ближайшее время'
    });
  };

  const handleLike = (profileId: number) => {
    if (likesLeft <= 0) {
      toast({
        title: 'Лимит лайков исчерпан',
        description: 'Сегодня доступно 15 лайков. Приходите завтра!',
        variant: 'destructive'
      });
      return;
    }

    setLikesLeft(prev => prev - 1);
    
    const isMutual = Math.random() > 0.7;
    
    if (isMutual) {
      setMatches(prev => [...prev, {
        profileId,
        mutualLike: true,
        username: '@' + sampleProfiles.find(p => p.id === profileId)?.name.toLowerCase()
      }]);
      
      toast({
        title: '💜 Взаимная симпатия!',
        description: `Вы можете написать: ${sampleProfiles.find(p => p.id === profileId)?.name}`,
      });
    } else {
      setMatches(prev => [...prev, { profileId, mutualLike: false }]);
      toast({
        title: 'Лайк отправлен',
        description: 'Если человек лайкнет вас в ответ — вы узнаете',
      });
    }

    if (currentProfileIndex < sampleProfiles.length - 1) {
      setCurrentProfileIndex(prev => prev + 1);
    } else {
      setCurrentProfileIndex(0);
    }
  };

  const handleSkip = () => {
    if (currentProfileIndex < sampleProfiles.length - 1) {
      setCurrentProfileIndex(prev => prev + 1);
    } else {
      setCurrentProfileIndex(0);
    }
  };

  const handleReport = () => {
    toast({
      title: 'Жалоба отправлена',
      description: 'Модератор рассмотрит её в ближайшее время'
    });
  };

  if (view === 'onboarding') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md p-6 border-2">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
              <Icon name="Heart" size={32} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Знакомства для подростков</h1>
            <p className="text-muted-foreground text-sm">Создайте анкету для начала</p>
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Имя *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Как тебя зовут?"
              />
            </div>

            <div>
              <Label htmlFor="age">Возраст *</Label>
              <Input
                id="age"
                type="number"
                min="13"
                max="19"
                value={formData.age}
                onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                placeholder="13-19 лет"
              />
            </div>

            <div>
              <Label htmlFor="city">Город *</Label>
              <Input
                id="city"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                placeholder="Москва"
              />
            </div>

            <div>
              <Label>Пол *</Label>
              <RadioGroup
                value={formData.gender}
                onValueChange={(value) => setFormData({ ...formData, gender: value as 'male' | 'female' })}
                className="flex gap-4 mt-2"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="male" id="male" />
                  <Label htmlFor="male">Парень</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="female" id="female" />
                  <Label htmlFor="female">Девушка</Label>
                </div>
              </RadioGroup>
            </div>

            <div>
              <Label htmlFor="photo">Фото (URL) *</Label>
              <Input
                id="photo"
                value={formData.photo}
                onChange={(e) => setFormData({ ...formData, photo: e.target.value })}
                placeholder="https://example.com/photo.jpg"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Будет проверено модератором
              </p>
            </div>

            <div>
              <Label htmlFor="bio">О себе</Label>
              <Input
                id="bio"
                value={formData.bio}
                onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                placeholder="Расскажи немного о себе"
              />
            </div>

            <Button onClick={handleSubmitProfile} className="w-full" size="lg">
              Создать анкету
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const currentProfile = sampleProfiles[currentProfileIndex];

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
              <Icon name="Heart" size={20} className="text-white" />
            </div>
            <span className="font-bold text-lg">Dating Bot</span>
          </div>
          
          <div className="flex items-center gap-4">
            <Badge variant="secondary" className="gap-2">
              <Icon name="Sparkles" size={16} />
              {likesLeft}/15 лайков
            </Badge>
            
            {myProfile && (
              <Badge variant={myProfile.status === 'approved' ? 'default' : 'secondary'}>
                {myProfile.status === 'pending' && 'На модерации'}
                {myProfile.status === 'approved' && 'Одобрено'}
                {myProfile.status === 'rejected' && 'Отклонено'}
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 max-w-2xl">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="browse">
              <Icon name="Search" size={16} className="mr-2" />
              Поиск
            </TabsTrigger>
            <TabsTrigger value="matches">
              <Icon name="Users" size={16} className="mr-2" />
              Взаимные
            </TabsTrigger>
            <TabsTrigger value="profile">
              <Icon name="User" size={16} className="mr-2" />
              Профиль
            </TabsTrigger>
            <TabsTrigger value="help">
              <Icon name="Info" size={16} className="mr-2" />
              Помощь
            </TabsTrigger>
          </TabsList>

          <TabsContent value="browse" className="mt-6">
            <Card className="border-2 overflow-hidden">
              <div className="aspect-square bg-muted relative">
                <img 
                  src={currentProfile.photo} 
                  alt={currentProfile.name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6 text-white">
                  <h2 className="text-3xl font-bold mb-1">{currentProfile.name}, {currentProfile.age}</h2>
                  <p className="flex items-center gap-2 text-sm mb-2">
                    <Icon name="MapPin" size={16} />
                    {currentProfile.city}
                  </p>
                  {currentProfile.bio && (
                    <p className="text-sm opacity-90">{currentProfile.bio}</p>
                  )}
                </div>
              </div>
              
              <div className="p-6">
                <div className="flex gap-3">
                  <Button 
                    variant="outline" 
                    size="lg" 
                    className="flex-1"
                    onClick={handleSkip}
                  >
                    <Icon name="X" size={20} className="mr-2" />
                    Пропустить
                  </Button>
                  
                  <Button 
                    size="lg" 
                    className="flex-1"
                    onClick={() => handleLike(currentProfile.id)}
                    disabled={likesLeft <= 0}
                  >
                    <Icon name="Heart" size={20} className="mr-2" />
                    Лайк
                  </Button>
                </div>

                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="w-full mt-3"
                  onClick={handleReport}
                >
                  <Icon name="Flag" size={16} className="mr-2" />
                  Пожаловаться
                </Button>

                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center justify-between text-sm text-muted-foreground mb-2">
                    <span>Прогресс сегодня</span>
                    <span>{15 - likesLeft}/15</span>
                  </div>
                  <Progress value={((15 - likesLeft) / 15) * 100} />
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="matches" className="mt-6">
            <Card className="p-6 border-2">
              <h2 className="text-xl font-bold mb-4">Взаимные симпатии</h2>
              
              {matches.filter(m => m.mutualLike).length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Icon name="Heart" size={48} className="mx-auto mb-4 opacity-20" />
                  <p>Пока нет взаимных лайков</p>
                  <p className="text-sm mt-2">Продолжайте смотреть анкеты!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {matches.filter(m => m.mutualLike).map((match) => {
                    const profile = sampleProfiles.find(p => p.id === match.profileId);
                    if (!profile) return null;
                    
                    return (
                      <div key={match.profileId} className="flex items-center gap-4 p-4 border rounded-lg">
                        <Avatar className="w-16 h-16">
                          <AvatarImage src={profile.photo} />
                          <AvatarFallback>{profile.name[0]}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <h3 className="font-bold">{profile.name}, {profile.age}</h3>
                          <p className="text-sm text-muted-foreground">{profile.city}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-mono text-primary">{match.username}</p>
                          <Button size="sm" variant="outline" className="mt-2">
                            Написать
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="profile" className="mt-6">
            <Card className="p-6 border-2">
              <h2 className="text-xl font-bold mb-4">Моя анкета</h2>
              
              {myProfile && (
                <div className="space-y-4">
                  <div className="flex items-start gap-4">
                    <Avatar className="w-24 h-24">
                      <AvatarImage src={myProfile.photo} />
                      <AvatarFallback>{myProfile.name[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <h3 className="text-2xl font-bold">{myProfile.name}, {myProfile.age}</h3>
                      <p className="text-muted-foreground flex items-center gap-2 mt-1">
                        <Icon name="MapPin" size={16} />
                        {myProfile.city}
                      </p>
                      <Badge className="mt-2">
                        {myProfile.gender === 'male' ? 'Парень' : 'Девушка'}
                      </Badge>
                    </div>
                  </div>

                  {myProfile.bio && (
                    <div>
                      <Label>О себе</Label>
                      <p className="mt-1">{myProfile.bio}</p>
                    </div>
                  )}

                  <div className="pt-4 border-t">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon name="Shield" size={20} />
                      <span className="font-semibold">Статус модерации</span>
                    </div>
                    <Badge variant={myProfile.status === 'approved' ? 'default' : 'secondary'} className="text-sm">
                      {myProfile.status === 'pending' && '⏳ Проверяется администратором'}
                      {myProfile.status === 'approved' && '✓ Анкета одобрена'}
                      {myProfile.status === 'rejected' && '✗ Отклонено'}
                    </Badge>
                  </div>

                  <Button variant="outline" className="w-full" onClick={() => setView('onboarding')}>
                    Редактировать анкету
                  </Button>
                </div>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="help" className="mt-6">
            <Card className="p-6 border-2">
              <h2 className="text-xl font-bold mb-4">Помощь и правила</h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <Icon name="Info" size={18} />
                    Как работает бот?
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Создайте анкету, просматривайте профили других пользователей и ставьте лайки. 
                    При взаимной симпатии откроется username для общения.
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <Icon name="Sparkles" size={18} />
                    Лимиты
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Доступно 15 лайков в день. Лимит обновляется каждые 24 часа.
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <Icon name="Shield" size={18} />
                    Модерация
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Все анкеты и фото проверяются администратором перед публикацией. 
                    Это обеспечивает безопасность всех пользователей.
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <Icon name="Flag" size={18} />
                    Жалобы
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Если заметили нарушение — нажмите "Пожаловаться". 
                    Модератор рассмотрит обращение в течение 24 часов.
                  </p>
                </div>

                <div className="pt-4 border-t">
                  <Button variant="outline" className="w-full">
                    <Icon name="MessageCircle" size={18} className="mr-2" />
                    Связаться с поддержкой
                  </Button>
                </div>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
